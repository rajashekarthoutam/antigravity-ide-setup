"""
SQLite FTS5 Virtual Context Vault (`ctx://<sha256[:12]>`) for Antigravity IDE.

Stores redacted oversized tool outputs in short-lived WAL SQLite connections with
Porter-stemming BM25 search, FTS5 syntax escaping, FIFO row capping, and
in-memory fallback when disk DB is unavailable.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any

from text_filters import (
    DEFAULT_VIRTUALIZE_CHARS,
    DEFAULT_VIRTUALIZE_LINES,
    cli_compress,
    count_tokens_safe,
    elide_output,
    redact_secrets,
    resolve_vault_db_path,
)

MAX_VAULT_ROWS = 2000
MAX_SLICE_LINES = 150


def _fts5_tokens(query: str) -> list[str]:
    """Extract safe alphanumeric/underscore search tokens (eliminates FTS5 syntax errors)."""
    return re.findall(r"[A-Za-z0-9_]+", query or "")


class ContextVirtualizer:
    """Short-lived WAL SQLite FTS5 vault mapping oversized outputs to `ctx://` handles."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        max_rows: int = MAX_VAULT_ROWS,
    ) -> None:
        self._explicit_db = Path(db_path).expanduser() if db_path else None
        self.max_rows = max(50, max_rows)
        self._mem_vault: dict[str, dict[str, Any]] = {}

    @property
    def db_path(self) -> Path:
        return resolve_vault_db_path(self._explicit_db)

    def _connect(self) -> sqlite3.Connection:
        path = self.db_path
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vault (
                handle TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                command TEXT NOT NULL,
                content TEXT NOT NULL,
                line_count INTEGER NOT NULL,
                byte_size INTEGER NOT NULL,
                token_count INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS vault_fts USING fts5(
                handle UNINDEXED,
                label,
                content,
                tokenize='porter unicode61'
            )
            """
        )
        return conn

    def _prune_old_rows(self, conn: sqlite3.Connection) -> None:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM vault").fetchone()
        total = int(row["cnt"]) if row else 0
        excess = total - self.max_rows
        if excess <= 0:
            return
        victims = conn.execute(
            "SELECT handle FROM vault ORDER BY created_at ASC LIMIT ?", (excess,)
        ).fetchall()
        handles = [r["handle"] for r in victims]
        if handles:
            placeholders = ",".join("?" for _ in handles)
            conn.execute(
                f"DELETE FROM vault_fts WHERE handle IN ({placeholders})", handles
            )
            conn.execute(f"DELETE FROM vault WHERE handle IN ({placeholders})", handles)

    def virtualize_output(
        self,
        content: str,
        label: str = "",
        command: str = "",
        threshold_chars: int = DEFAULT_VIRTUALIZE_CHARS,
        threshold_lines: int = DEFAULT_VIRTUALIZE_LINES,
    ) -> dict[str, Any]:
        """Redact secrets and store oversized outputs in SQLite FTS5."""
        raw_text = (content or "").replace("\r\n", "\n")
        safe_text = redact_secrets(raw_text)
        compressed = cli_compress(safe_text, command=command)
        lines = safe_text.splitlines()
        raw_tokens = count_tokens_safe(raw_text)

        if len(safe_text) <= threshold_chars and len(lines) <= threshold_lines:
            digest = compressed or safe_text
            return {
                "status": "INLINE",
                "virtualized": False,
                "storage": "inline",
                "handle": "",
                "label": label or command or "output",
                "digest": digest,
                "raw_tokens": raw_tokens,
                "digest_tokens": count_tokens_safe(digest),
                "line_count": len(lines),
            }

        digest_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()[:12]
        digest = elide_output(compressed, head_lines=5, tail_lines=5, max_chars=360)
        digest_tokens = count_tokens_safe(digest)
        clean_label = label or command or "tool_output"
        now = time.time()

        try:
            handle = f"ctx://{digest_hash}"
            with closing(self._connect()) as conn, conn:
                conn.execute("DELETE FROM vault_fts WHERE handle = ?", (handle,))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO vault
                    (handle, label, command, content, line_count, byte_size, token_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        handle,
                        clean_label,
                        command or "",
                        safe_text,
                        len(lines),
                        len(safe_text.encode("utf-8")),
                        raw_tokens,
                        now,
                    ),
                )
                conn.execute(
                    "INSERT INTO vault_fts (handle, label, content) VALUES (?, ?, ?)",
                    (handle, clean_label, safe_text),
                )
                self._prune_old_rows(conn)
            storage = "sqlite_wal_fts5"
            status = "VIRTUALIZED"
        except sqlite3.Error as exc:
            handle = f"mem://{digest_hash}"
            self._mem_vault[handle] = {
                "handle": handle,
                "label": clean_label,
                "command": command or "",
                "content": safe_text,
                "line_count": len(lines),
                "token_count": raw_tokens,
                "created_at": now,
                "error": str(exc),
            }
            storage = "memory_fallback"
            status = "DEGRADED_MEMORY"

        return {
            "status": status,
            "virtualized": True,
            "storage": storage,
            "handle": handle,
            "label": clean_label,
            "digest": f"[{handle} | {len(lines)}L, {raw_tokens}tok]\n{digest}",
            "raw_tokens": raw_tokens,
            "digest_tokens": digest_tokens,
            "line_count": len(lines),
        }

    def search_virtual_context(
        self, query: str, handle: str = "", limit: int = 5
    ) -> dict[str, Any]:
        """Search virtualized outputs safely with FTS5 BM25 + OR/LIKE fallbacks."""
        capped = max(1, min(int(limit or 5), 20))
        tokens = _fts5_tokens(query)
        hits: list[dict[str, Any]] = []

        if (handle and handle.startswith("mem://")) or self._mem_vault:
            for key, entry in list(self._mem_vault.items())[::-1]:
                if handle and key != handle:
                    continue
                low = entry["content"].lower()
                if not tokens or any(t.lower() in low for t in tokens):
                    hits.append(
                        {
                            "handle": key,
                            "label": entry["label"],
                            "line_count": entry["line_count"],
                            "token_count": entry["token_count"],
                            "snippet": elide_output(entry["content"], 3, 3, 200),
                            "score": 0.0,
                        }
                    )
            if handle.startswith("mem://") or (hits and not self.db_path.exists()):
                return {"status": "OK", "query": query, "matches": hits[:capped]}

        if not self.db_path.exists():
            return {"status": "OK", "query": query, "matches": hits[:capped]}

        try:
            with closing(self._connect()) as conn:
                if not tokens:
                    sql = "SELECT handle, label, line_count, token_count, substr(content, 1, 180) AS snippet FROM vault"
                    params: list[Any] = []
                    if handle:
                        sql += " WHERE handle = ?"
                        params.append(handle)
                    sql += " ORDER BY created_at DESC LIMIT ?"
                    params.append(capped)
                    for r in conn.execute(sql, params).fetchall():
                        hits.append(
                            {
                                "handle": r["handle"],
                                "label": r["label"],
                                "line_count": r["line_count"],
                                "token_count": r["token_count"],
                                "snippet": r["snippet"],
                                "score": 0.0,
                            }
                        )
                    return {"status": "OK", "query": query, "matches": hits[:capped]}

                rows = []
                for expr in (
                    " AND ".join(f'"{t}"' for t in tokens[:8]),
                    " OR ".join(f'"{t}"' for t in tokens[:8]),
                ):
                    try:
                        base_sql = (
                            "SELECT v.handle, v.label, v.line_count, v.token_count, "
                            "snippet(vault_fts, 2, '>>', '<<', '...', 20) AS snippet, "
                            "bm25(vault_fts) AS score "
                            "FROM vault_fts JOIN vault v ON v.handle = vault_fts.handle "
                            "WHERE vault_fts MATCH ?"
                        )
                        q_params: list[Any] = [expr]
                        if handle:
                            base_sql += " AND v.handle = ?"
                            q_params.append(handle)
                        base_sql += " ORDER BY score ASC LIMIT ?"
                        q_params.append(capped)
                        rows = conn.execute(base_sql, q_params).fetchall()
                        if rows:
                            break
                    except sqlite3.OperationalError:
                        rows = []
                if not rows:
                    like_clauses = " OR ".join("content LIKE ?" for _ in tokens[:4])
                    like_params: list[Any] = [f"%{t}%" for t in tokens[:4]]
                    like_sql = (
                        "SELECT handle, label, line_count, token_count, "
                        f"substr(content, 1, 200) AS snippet FROM vault WHERE ({like_clauses})"
                    )
                    if handle:
                        like_sql += " AND handle = ?"
                        like_params.append(handle)
                    like_sql += " ORDER BY created_at DESC LIMIT ?"
                    like_params.append(capped)
                    rows = conn.execute(like_sql, like_params).fetchall()

                for r in rows:
                    hits.append(
                        {
                            "handle": r["handle"],
                            "label": r["label"],
                            "line_count": r["line_count"],
                            "token_count": r["token_count"],
                            "snippet": r["snippet"],
                            "score": round(float(r["score"]), 4)
                            if "score" in r
                            else 0.0,
                        }
                    )
        except sqlite3.Error as exc:
            return {
                "status": "ERROR",
                "error": str(exc),
                "query": query,
                "matches": hits[:capped],
            }
        return {"status": "OK", "query": query, "matches": hits[:capped]}

    def fetch_virtual_slice(
        self, handle: str, start_line: int = 1, end_line: int = 60
    ) -> dict[str, Any]:
        """Fetch a bounded line slice (<= 150 lines) from a stored context handle."""
        s_line = max(1, int(start_line or 1))
        requested_end = int(end_line or (s_line + 59))
        e_line = min(s_line + MAX_SLICE_LINES - 1, max(s_line, requested_end))

        content: str | None = None
        label = ""
        if handle in self._mem_vault:
            content = self._mem_vault[handle]["content"]
            label = self._mem_vault[handle]["label"]
        elif self.db_path.exists():
            try:
                with closing(self._connect()) as conn:
                    row = conn.execute(
                        "SELECT label, content FROM vault WHERE handle = ?", (handle,)
                    ).fetchone()
                    if row:
                        label = row["label"]
                        content = row["content"]
            except sqlite3.Error as exc:
                return {"status": "ERROR", "handle": handle, "error": str(exc)}

        if content is None:
            return {
                "status": "NOT_FOUND",
                "handle": handle,
                "error": "Handle not found",
            }

        lines = content.splitlines()
        total = len(lines)
        actual_end = min(e_line, total)
        sliced = lines[s_line - 1 : actual_end]
        return {
            "status": "OK",
            "handle": handle,
            "label": label,
            "start_line": s_line,
            "end_line": actual_end,
            "total_lines": total,
            "has_more": actual_end < total,
            "content": "\n".join(f"{s_line + i}: {ln}" for i, ln in enumerate(sliced)),
        }


def virtualize_output(
    content: str,
    label: str = "",
    command: str = "",
    threshold_chars: int = DEFAULT_VIRTUALIZE_CHARS,
    threshold_lines: int = DEFAULT_VIRTUALIZE_LINES,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Convenience wrapper persisting oversized output to FTS5 virtual context vault."""
    return ContextVirtualizer(db_path=db_path).virtualize_output(
        content=content,
        label=label,
        command=command,
        threshold_chars=threshold_chars,
        threshold_lines=threshold_lines,
    )


def search_virtual_context(
    query: str,
    handle: str = "",
    limit: int = 5,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Convenience wrapper querying the virtual context vault with BM25."""
    return ContextVirtualizer(db_path=db_path).search_virtual_context(
        query=query, handle=handle, limit=limit
    )


def fetch_virtual_slice(
    handle: str,
    start_line: int = 1,
    end_line: int = 60,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Convenience wrapper fetching a bounded line window from a context handle."""
    return ContextVirtualizer(db_path=db_path).fetch_virtual_slice(
        handle=handle, start_line=start_line, end_line=end_line
    )
