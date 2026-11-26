"""
Deterministic Zero-LLM Text Filters, Redaction & Token Counting for God-Mode MCP.

Pure helper module (zero internal MCP imports) shared across `infinite_context`,
`security_eval`, `code_nav`, `ops_helpers`, and `server`.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

try:
    import tiktoken
except Exception:  # pragma: no cover - offline fallback covered cleanly
    tiktoken = None  # type: ignore[assignment]

DEFAULT_VIRTUALIZE_CHARS = 1200
DEFAULT_VIRTUALIZE_LINES = 35

_ENC: Any = None
_ENC_UNAVAILABLE = False

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (
        re.compile(r"\bsk-(?:proj-|live-|test-)?[A-Za-z0-9_-]{20,}\b"),
        "[REDACTED_API_KEY]",
    ),
    (
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
        "[REDACTED_GH_TOKEN]",
    ),
    (re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (
        re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._+/=-]{16,}\b", re.IGNORECASE),
        r"\1 [REDACTED_TOKEN]",
    ),
    (
        re.compile(
            r"(\b(?:password|passwd|api[_-]?key|secret|client_secret|access_token)\s*[:=]\s*['\"]?)([A-Za-z0-9_/+=-]{12,})(['\"]?)",
            re.IGNORECASE,
        ),
        r"\1[REDACTED_SECRET]\3",
    ),
]

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
_DIAGNOSTIC_RE = re.compile(
    r'(?:error|exception|traceback|failed|fatal|panic|assert(?:ion)?|warning:|exit code|syntaxerror|typeerror|valueerror|nameerror|importerror|attributeerror|keyerror|\bFAIL\b|\bERROR\b|\^\^\^|File "[^"]+", line \d+|\d+\s+(?:passed|failed|skipped|errors?)|^---\s|^\+\+\+\s|^@@\s)',
    re.IGNORECASE,
)
_NOISE_LINE_RE = re.compile(
    r"^(?:"
    r"\s*(?:Downloading|Collecting|Fetching|Resolving deltas|Unpacking objects|"
    r"Preparing metadata|Using cached|Requirement already satisfied|Removing intermediate|"
    r"added \d+ packages? in)\b.*"
    r"|\s*\d{1,3}%\s*[|\u2588\u2593\u2591#=->\s]+.*"
    r"|\s*[.sSx]+\s*"
    r"|\s*(?:PASSED|ok)\s*"
    r"|\s*ok\s+\S+.*"
    r"|\s*\.\.\.\s*ok\s*"
    r")$"
)


def resolve_home_dir() -> Path:
    """Resolve active Gemini home directory cleanly (supports test overrides)."""
    override = os.environ.get("GOD_MODE_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".gemini"


def resolve_vault_db_path(db_path: str | Path | None = None) -> Path:
    """Unified vault path precedence: arg > GOD_MODE_VAULT_DB > GOD_MODE_HOME."""
    if db_path:
        return Path(db_path).expanduser()
    env_db = os.environ.get("GOD_MODE_VAULT_DB", "").strip()
    if env_db:
        return Path(env_db).expanduser()
    return resolve_home_dir() / "config" / "context_vault.db"


def count_tokens_safe(text: str) -> int:
    """Count tokens using cl100k_base with deterministic offline heuristic fallback."""
    if not text:
        return 0
    global _ENC, _ENC_UNAVAILABLE
    if not _ENC_UNAVAILABLE and _ENC is None and tiktoken is not None:
        try:
            _ENC = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENC_UNAVAILABLE = True
    if _ENC is not None:
        return len(_ENC.encode(text, disallowed_special=()))
    return max(1, (len(text) + 3) // 4)


def redact_secrets(text: str) -> str:
    """Redact credentials, API tokens, and private keys before persistence or output."""
    if not text:
        return text
    cleaned = text
    for pattern, repl in _SECRET_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    return cleaned


def elide_output(
    text: str,
    head_lines: int = 15,
    tail_lines: int = 15,
    max_chars: int = DEFAULT_VIRTUALIZE_CHARS,
) -> str:
    """Trim large text to bounded head/tail lines while clamping single-line dumps."""
    if not text:
        return ""
    norm = text.replace("\r\n", "\n")
    lines = norm.splitlines()
    if len(norm) <= max_chars and len(lines) <= head_lines + tail_lines + 4:
        return norm

    def _clamp_line(line: str) -> str:
        return line if len(line) <= 220 else line[:217] + "..."

    if len(lines) <= head_lines + tail_lines:
        clamped = [_clamp_line(ln) for ln in lines]
        joined = "\n".join(clamped)
        if len(joined) <= max_chars:
            return joined
        half = max(60, (max_chars - 50) // 2)
        return (
            joined[:half]
            + f"\n... [elided {len(norm) - max_chars} chars] ...\n"
            + joined[-half:]
        )

    head = [_clamp_line(ln) for ln in lines[:head_lines]]
    tail = [_clamp_line(ln) for ln in lines[-tail_lines:]]
    omitted_lines = max(0, len(lines) - head_lines - tail_lines)
    combined = "\n".join(
        head
        + [f"... [elided {omitted_lines} lines / {len(norm)} chars total] ..."]
        + tail
    )
    if len(combined) > max_chars:
        half = max(60, (max_chars - 50) // 2)
        return (
            combined[:half]
            + f"\n... [elided {len(norm)} chars total] ...\n"
            + combined[-half:]
        )
    return combined


def extract_error_tail(text: str, max_chars: int = 320) -> str:
    """Extract highest-signal diagnostic snippet for failed calls without losing errors."""
    if not text:
        return "command failed (empty output)"
    norm = text.replace("\r\n", "\n")
    lines = [ln.strip() for ln in norm.splitlines() if ln.strip()]
    if not lines:
        return "command failed"
    diag_idx = [i for i, ln in enumerate(lines) if _DIAGNOSTIC_RE.search(ln)]
    if diag_idx:
        picked: list[str] = []
        seen: set[int] = set()
        for idx in diag_idx[-4:]:
            for sub in (idx - 1, idx, idx + 1):
                if 0 <= sub < len(lines) and sub not in seen:
                    seen.add(sub)
                    picked.append(lines[sub])
        snippet = " | ".join(picked)
    else:
        snippet = " | ".join(lines[-3:])
    return snippet[:max_chars] + ("..." if len(snippet) > max_chars else "")


def cli_compress(text: str, command: str = "") -> str:
    """
    Deterministic 0-LLM CLI output compressor (rtk-inspired).
    Strips ANSI codes, CR spinner frames, and download/passing noise while
    unconditionally preserving tracebacks, failures, summary counts, and diffs.
    """
    if not text:
        return ""
    norm = text.replace("\r\n", "\n")
    raw_lines = [ln.rsplit("\r", 1)[-1] for ln in norm.split("\n")]
    clean_lines = [_ANSI_RE.sub("", ln).rstrip() for ln in raw_lines]

    is_diff = "diff" in (command or "").lower() or any(
        ln.startswith(("diff --git ", "--- ", "+++ ", "@@ ")) for ln in clean_lines[:40]
    )
    keep_mask = [False] * len(clean_lines)
    for idx, ln in enumerate(clean_lines):
        if _DIAGNOSTIC_RE.search(ln) or (
            is_diff and ln.startswith(("diff ", "+", "-", "@@"))
        ):
            keep_mask[idx] = True
            if idx > 0 and not _NOISE_LINE_RE.match(clean_lines[idx - 1]):
                keep_mask[idx - 1] = True
            if idx + 1 < len(clean_lines) and not _NOISE_LINE_RE.match(
                clean_lines[idx + 1]
            ):
                keep_mask[idx + 1] = True

    out_lines: list[str] = []
    omitted_noise = 0
    prev_blank = False
    for idx, ln in enumerate(clean_lines):
        if not ln.strip():
            if out_lines and not prev_blank:
                out_lines.append("")
            prev_blank = True
            continue
        if not keep_mask[idx] and _NOISE_LINE_RE.match(ln):
            omitted_noise += 1
            continue
        prev_blank = False
        out_lines.append(ln)

    while out_lines and not out_lines[-1].strip():
        out_lines.pop()

    if omitted_noise > 0:
        out_lines.append(
            f"[cli_compress: filtered {omitted_noise} noise/progress lines]"
        )
    if not out_lines:
        return elide_output(redact_secrets(norm), max_chars=800)
    return "\n".join(out_lines)
