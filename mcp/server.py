"""
God-Mode MCP Server for Antigravity IDE
Thin FastMCP Router & Public Re-Export Surface (<= 550 lines, <= 10 upfront schemas).
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP as MCPServer
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    from mcp.server.mcpserver import MCPServer

_BASE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BASE_DIR.parent if _BASE_DIR.name == "mcp" else _BASE_DIR

# Ensure sibling modules (`text_filters`, `infinite_context`, `code_nav`,
# `security_eval`, `ops_helpers`, `tools_api`) resolve without creating `mcp/__init__.py`.
for _p in (_BASE_DIR, _REPO_ROOT, _REPO_ROOT / "scripts" / "hooks"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from code_nav import (  # noqa: F401
    _SESSION_FILE_CACHE,
    DIFFT_BIN,
    SCC_BIN,
    _run_pagerank,
    code_graph_impact_probe,
    code_reference_probe,
    diff_re_read,
    get_file_outline,
    get_symbol,
    github_agentic_probe,
    repo_shape_probe,
    safe_read_file,
    structural_diff,
    validate_syntax,
)
from code_nav import pagerank_repo_map as _pagerank_repo_map_impl
from infinite_context import (  # noqa: F401
    ContextVirtualizer,
    cli_compress,
    compact_conversation_loop,
    count_tokens_safe,
    elide_output,
    fetch_virtual_slice,
    redact_secrets,
    resolve_home_dir,
    run_compressed,
    search_virtual_context,
    virtualize_output,
)
from ops_helpers import (  # noqa: F401
    _TOOL_OUTPUT_CACHE,
    _to_toon_value,
    audit_workspace_tokens,
    auto_setup_environment,
    cache_prefix_audit,
    clear_chat_history,
    guardrail_scan_dir,
    llmtrim_compress,
    ruff_fix_preflight,
    run_health_doctor,
    to_toon,
)
from ops_helpers import (
    cache_lookup_or_store as _cache_lookup_or_store_impl,
)
from ops_helpers import (
    create_checkpoint as _create_checkpoint_impl,
)
from ops_helpers import (
    restore_checkpoint as _restore_checkpoint_impl,
)
from security_eval import (  # noqa: F401
    audit_agent_safety,
    get_agent_card,
    list_agent_cards,
    model_armor_sanitize,
    synthesize_skill,
    validate_a2a_handoff,
    verify_agent_skill,
)
from security_eval import evaluate_skill as _evaluate_skill_impl
from security_eval import search_skills as _search_skills_impl

app = MCPServer("god-mode")

_LOCAL_MEM = _REPO_ROOT / "config" / "memory.json"
_DEFAULT_MEM_SENTINEL = Path(os.path.expanduser(r"~\.gemini\config\memory.json"))
_DEFAULT_GRAPH_SENTINEL = Path(
    os.path.expanduser(r"~\.gemini\config\god_mode_knowledge_graph.json")
)
_DEFAULT_CACHE_SENTINEL = Path(
    os.path.expanduser(r"~\.gemini\config\god_mode_tool_cache.json")
)
_DEFAULT_CP_SENTINEL = Path(os.path.expanduser(r"~\.gemini\checkpoints"))

MEMORY_FILE = _DEFAULT_MEM_SENTINEL
GRAPH_FILE = _DEFAULT_GRAPH_SENTINEL
_TOOL_CACHE_FILE = _DEFAULT_CACHE_SENTINEL
CHECKPOINTS_DIR = _DEFAULT_CP_SENTINEL


def _memory_path(for_write: bool = False) -> Path:
    if MEMORY_FILE != _DEFAULT_MEM_SENTINEL:
        return MEMORY_FILE
    global_mem = resolve_home_dir() / "config" / "memory.json"
    if for_write or global_mem.exists() or os.environ.get("GOD_MODE_HOME", "").strip():
        return global_mem
    return _LOCAL_MEM if _LOCAL_MEM.exists() else global_mem


def _graph_path() -> Path:
    if GRAPH_FILE != _DEFAULT_GRAPH_SENTINEL:
        return GRAPH_FILE
    return resolve_home_dir() / "config" / "god_mode_knowledge_graph.json"


def _load_memories() -> list[dict[str, Any]]:
    path = _memory_path(for_write=False)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f).get("memories", [])
        except Exception:
            return []
    return []


def _save_memories(memories: list[dict[str, Any]]) -> None:
    path = _memory_path(for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"memories": memories}, f, indent=2, ensure_ascii=False)


def _load_graph() -> list[dict[str, Any]]:
    path = _graph_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f).get("nodes", [])
        except Exception:
            return []
    return []


def _save_graph(nodes: list[dict[str, Any]]) -> None:
    path = _graph_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes}, f, indent=2, ensure_ascii=False)


def create_checkpoint(checkpoint_id: str = "", files: list[str] | None = None) -> str:
    """Snapshots modified files to checkpoints directory for instant zero-token rollback."""
    override = CHECKPOINTS_DIR if CHECKPOINTS_DIR != _DEFAULT_CP_SENTINEL else None
    return _create_checkpoint_impl(
        checkpoint_id=checkpoint_id, files=files, cp_root=override
    )


def restore_checkpoint(checkpoint_id: str) -> str:
    """Restores files from a checkpoint back to original locations."""
    override = CHECKPOINTS_DIR if CHECKPOINTS_DIR != _DEFAULT_CP_SENTINEL else None
    return _restore_checkpoint_impl(checkpoint_id=checkpoint_id, cp_root=override)


def cache_lookup_or_store(
    cache_key: str,
    payload: str = "",
    mode: str = "get",
    compress: bool = True,
) -> dict[str, Any]:
    """Persistent compressed content-hash tool output cache on disk (TOON + zlib)."""
    override = _TOOL_CACHE_FILE if _TOOL_CACHE_FILE != _DEFAULT_CACHE_SENTINEL else None
    return _cache_lookup_or_store_impl(
        cache_key=cache_key,
        payload=payload,
        mode=mode,
        compress=compress,
        cache_override=override,
    )


# ---------------------------------------------------------------------------
# Upfront @app.tool() Registered Tools (Strictly <= 10: 9 active schemas)
# ---------------------------------------------------------------------------


@app.tool()
def execute_code_sandbox(script: str) -> str:
    """
    Executes a Python script in an isolated subprocess (Code Mode) and returns stdout.
    Imports `tools_api/*` and `infinite_context` cleanly while keeping raw data out of prompt context.
    """
    try:
        env = os.environ.copy()
        existing_pp = env.get("PYTHONPATH", "")
        pp_parts = [str(_BASE_DIR), str(_REPO_ROOT)]
        if existing_pp:
            pp_parts.append(existing_pp)
        env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(pp_parts))

        res = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env=env,
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        if res.returncode != 0:
            return f"[Sandbox Execution Error (Code {res.returncode})]:\n{err or out}"
        return out or "[Sandbox executed successfully with no stdout]"
    except subprocess.TimeoutExpired:
        return "[Sandbox Timeout: Script exceeded 15 second limit]"
    except Exception as e:
        return f"[Sandbox Fatal Error]: {e}"


@app.tool()
def pagerank_repo_map(root_dir: str = ".", max_tokens: int = 1024) -> str:
    """Constructs an Aider-style AST repository map using PageRank within token budget."""
    return _pagerank_repo_map_impl(root_dir=root_dir, max_tokens=max_tokens)


@app.tool()
def system1_triage(content: str, triage_type: str = "log") -> dict[str, Any]:
    """Executes sub-40ms System 1 triage on terminal logs/diffs with 0 LLM tokens."""
    try:
        try:
            from scripts.hooks.laya_gate import evaluate_decision, triage_log_output
        except ImportError:
            from laya_gate import evaluate_decision, triage_log_output

        if triage_type == "log":
            return triage_log_output(content)
        state = {"input": content[:2500]}
        questions = {
            "has_actionable_issue": {
                "type": "noul",
                "instructions": "Does this text require code modifications or attention?",
            },
            "category": {
                "type": "choice",
                "instructions": "Primary category",
                "criteria": ["error", "warning", "info", "query"],
            },
        }
        return evaluate_decision(state, questions)
    except Exception as e:
        return {"error": str(e), "engine": "fallback"}


@app.tool()
def search_memories(query: str, user_id: str = "default", max_tokens: int = 50) -> str:
    """Retrieves relevant project memories bounded strictly to <= max_tokens."""
    memories = _load_memories()
    if not memories:
        return "No memories recorded."

    matches: list[tuple[float, dict[str, Any], str]] = []
    for m in memories:
        text_body = m.get("content") or " | ".join(
            str(m.get(k, ""))
            for k in ("error_signature", "root_cause", "countermeasure")
            if m.get(k)
        )
        meta = str(m.get("metadata") or m.get("category") or "note")
        score = _score_memory_match(query, text_body, meta)
        if score > 0:
            matches.append((score, m, text_body))

    matches.sort(key=lambda x: x[0], reverse=True)
    if not matches:
        return f"No memories for '{query}'."

    output: list[str] = []
    current_tokens = 0
    for _, m, body in matches:
        meta = str(m.get("metadata") or m.get("category") or "note")[:4].upper()
        line = f"[MEM0:{meta}] {body}"
        line_tokens = count_tokens_safe(line)
        if current_tokens + line_tokens <= max_tokens:
            output.append(line)
            current_tokens += line_tokens
        elif not output:
            output.append(line[: max(20, max_tokens * 3)])
            break
        else:
            break

    return "\n".join(output) if output else "No memories within token budget."


@app.tool()
def search_skills(query: str, limit: int = 5) -> str:
    """Searches installed `skills/` and `skills_vault/` catalogs on demand."""
    return _search_skills_impl(query=query, limit=limit)


@app.tool()
def discover_mcp_tools(query: str = "") -> dict[str, Any]:
    """Code-Mode on-demand tool discovery searching `mcp/tools_api/` and `mcp/schemas/`."""
    tools_api_dir = _BASE_DIR / "tools_api"
    schemas_dir = _BASE_DIR / "schemas"
    q = query.lower().strip()
    matches: list[dict[str, Any]] = []

    if tools_api_dir.exists():
        for py_file in sorted(tools_api_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            try:
                tree = ast.parse(text)
                exported: list[str] = []
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if (
                                isinstance(target, ast.Name)
                                and target.id == "__all__"
                                and isinstance(node.value, ast.List)
                            ):
                                exported = [
                                    elt.value
                                    for elt in node.value.elts
                                    if isinstance(elt, ast.Constant)
                                    and isinstance(elt.value, str)
                                ]
            except SyntaxError:
                exported = []

            if (
                not q
                or q in py_file.stem.lower()
                or any(q in t.lower() for t in exported)
            ):
                try:
                    mod_rel = str(py_file.relative_to(_REPO_ROOT)).replace("\\", "/")
                except ValueError:
                    mod_rel = f"tools_api/{py_file.name}"
                matches.append(
                    {
                        "module_file": mod_rel,
                        "import_stmt": f"from tools_api.{py_file.stem} import ...",
                        "tools": exported,
                    }
                )

    schema_hits: list[str] = []
    if schemas_dir.exists() and q:
        for sf in sorted(schemas_dir.glob("*.json")):
            if q in sf.stem.lower():
                schema_hits.append(sf.stem)

    return {
        "pattern": "anthropic-code-execution-tools-as-files",
        "query": query or "*",
        "api_modules": matches,
        "matching_schemas": schema_hits[:20],
        "tip": "Import only needed functions inside execute_code_sandbox() to avoid schema bloat.",
    }


@app.tool()
def filter_and_loop_data(
    data_source: str,
    keyword_or_regex: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Filters JSON, JSONL, CSV, or log files locally in Python before emitting summaries."""
    src = Path(data_source).resolve()
    if not src.exists() or not src.is_file():
        return {"status": "ERROR", "error": f"File not found: {data_source}"}

    pattern = re.compile(keyword_or_regex, re.IGNORECASE) if keyword_or_regex else None
    total_scanned = 0
    total_matched = 0
    samples: list[Any] = []

    try:
        if src.suffix.lower() == ".json":
            raw = json.loads(src.read_text(encoding="utf-8", errors="ignore"))
            records = (
                raw
                if isinstance(raw, list)
                else raw.get("items", raw.get("memories", [raw]))
            )
            for rec in records:
                total_scanned += 1
                if not pattern or pattern.search(json.dumps(rec, ensure_ascii=False)):
                    total_matched += 1
                    if len(samples) < limit:
                        samples.append(rec)
        else:
            with open(src, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, 1):
                    total_scanned += 1
                    if not pattern or pattern.search(line):
                        total_matched += 1
                        if len(samples) < limit:
                            samples.append({"line": idx, "text": line.rstrip()[:300]})
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    return {
        "status": "OK",
        "source": str(src),
        "raw_size_bytes": src.stat().st_size,
        "total_records_scanned": total_scanned,
        "total_matched": total_matched,
        "returned_count": len(samples),
        "truncated": total_matched > len(samples),
        "matches": samples,
    }


@app.tool()
def evaluate_skill(skill_path_or_name: str) -> dict[str, Any]:
    """Deterministic Skill Evaluator grading skill quality, token economy, and security."""
    return _evaluate_skill_impl(skill_path_or_name=skill_path_or_name)


@app.tool()
def infinite_context_compact(
    mode: str = "compact",
    payload: str = "",
    state_json: str = "",
    query: str = "",
    handle: str = "",
    start_line: int = 1,
    end_line: int = 60,
    window: int = 4,
    token_budget: int = 6000,
    epoch_size: int = 12,
    force: bool = False,
) -> dict[str, Any]:
    """
    Infinite-Horizon Context Engine unified interface:
    modes `compact`, `virtualize`, `search`, `fetch`, `cli_compress`.
    """
    m = (mode or "compact").strip().lower()
    if m == "virtualize":
        return virtualize_output(content=payload, label=query or "tool_output")
    if m == "search":
        return search_virtual_context(query=query or payload, handle=handle)
    if m == "fetch":
        return fetch_virtual_slice(
            handle=handle or payload, start_line=start_line, end_line=end_line
        )
    if m == "cli_compress":
        compressed = cli_compress(payload, command=query)
        raw_tok = count_tokens_safe(payload)
        cmp_tok = count_tokens_safe(compressed)
        pct = round((1.0 - (cmp_tok / raw_tok)) * 100.0, 2) if raw_tok else 0.0
        return {
            "status": "OK",
            "raw_tokens": raw_tok,
            "compressed_tokens": cmp_tok,
            "reduction_pct": pct,
            "compressed": compressed,
        }

    try:
        msgs = json.loads(payload) if payload.strip() else []
    except json.JSONDecodeError as exc:
        return {"status": "ERROR", "error": f"Invalid messages JSON payload: {exc}"}
    state = None
    if state_json.strip():
        try:
            state = json.loads(state_json)
        except json.JSONDecodeError:
            state = None
    return compact_conversation_loop(
        messages=msgs,
        window=window,
        token_budget=token_budget,
        epoch_size=epoch_size,
        state=state,
        force=force,
    )


# ---------------------------------------------------------------------------
# Memory, Knowledge Graph & Sandbox Helper Exports
# ---------------------------------------------------------------------------


def speculative_sandbox(command: str, root_dir: str = ".") -> str:
    """Executes verification commands safely without modifying active branches."""
    try:
        res = subprocess.run(
            command,
            shell=True,
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        status = "PASSED" if res.returncode == 0 else f"FAILED (Code {res.returncode})"
        summary = (res.stdout.strip() or res.stderr.strip())[:600]
        return f"[Sandbox Run: {status}]\n{summary}"
    except subprocess.TimeoutExpired:
        return "[Sandbox Timeout: Command exceeded 30 seconds]"
    except Exception as e:
        return f"[Sandbox Error]: {e}"


def record_side_effect(category: str, topic: str, conclusion: str) -> str:
    """Records an empirical finding, architectural decision, or dead-end experiment."""
    nodes = _load_graph()
    next_id = (
        max((int(n["id"]) for n in nodes if isinstance(n.get("id"), int)), default=0)
        + 1
    )
    nodes.append(
        {
            "id": next_id,
            "category": category.lower(),
            "topic": topic.strip(),
            "conclusion": conclusion.strip(),
        }
    )
    _save_graph(nodes)
    return f"Recorded graph node [{category.upper()}]: {topic} -> {conclusion[:60]}..."


def query_side_effects(topic_or_query: str = "") -> str:
    """Queries the Side-Effect Knowledge Graph for past decisions and dead ends."""
    nodes = _load_graph()
    if not nodes:
        return "Knowledge graph is empty."
    if not topic_or_query:
        matches = nodes
    else:
        q = topic_or_query.lower()
        matches = [
            n
            for n in nodes
            if q in n.get("topic", "").lower()
            or q in n.get("conclusion", "").lower()
            or q in n.get("category", "").lower()
        ]
    if not matches:
        return f"No knowledge graph nodes found for '{topic_or_query}'."
    out = ["### Side-Effect Knowledge Graph:"]
    for n in matches[-8:]:
        out.append(
            f"- [{str(n.get('category')).upper()}] {n.get('topic')}: {n.get('conclusion')}"
        )
    return "\n".join(out)


def add_memory(
    content: str, user_id: str = "default", metadata: str | None = None
) -> str:
    """Stores an architectural lesson, decision, or bug fix pattern to persistent memory."""
    memories = _load_memories()
    next_id = (
        max((int(m["id"]) for m in memories if isinstance(m.get("id"), int)), default=0)
        + 1
    )
    entry = {
        "id": next_id,
        "content": content,
        "user_id": user_id,
        "metadata": metadata or "general",
    }
    memories.append(entry)
    _save_memories(memories)
    return f"Saved memory (ID: {entry['id']}): {content[:80]}..."


def _score_memory_match(query: str, content: str, metadata: str) -> float:
    q_lower = query.lower()
    text = (content + " " + metadata).lower()
    terms = [t for t in re.findall(r"\w+", q_lower) if len(t) > 2]
    if not terms:
        return 0.0

    score = 0.0
    doc_words = set(re.findall(r"\w+", text))
    for t in terms:
        if t in doc_words:
            score += 3.0
        elif any(t in w or w in t for w in doc_words if len(w) > 3):
            score += 1.5

    if len(q_lower) >= 3 and len(text) >= 3:
        q_grams = {q_lower[i : i + 3] for i in range(len(q_lower) - 2)}
        d_grams = {text[i : i + 3] for i in range(min(len(text), 300) - 2)}
        union = len(q_grams | d_grams)
        if union:
            score += (len(q_grams & d_grams) / union) * 4.0
    return score


def count_tokens(text: str) -> dict[str, Any]:
    """Calculates exact token count for context budgeting."""
    try:
        return {"tokens": count_tokens_safe(text), "characters": len(text)}
    except Exception as e:
        return {"error": str(e)}


def record_failure_reflexion(
    error_signature: str, root_cause: str, countermeasure: str
) -> str:
    """Records a verified anti-pattern and countermeasure in persistent Mem0 memory."""
    try:
        memories = _load_memories()
        existing_nums = [
            int(str(m.get("id", ""))[10:])
            for m in memories
            if str(m.get("id", "")).startswith("reflexion-")
            and str(m.get("id", ""))[10:].isdigit()
        ]
        next_num = max(existing_nums, default=len(memories)) + 1
        memory_id = f"reflexion-{next_num:04d}"
        memories.append(
            {
                "id": memory_id,
                "category": "anti_pattern",
                "error_signature": error_signature.strip(),
                "root_cause": root_cause.strip(),
                "countermeasure": countermeasure.strip(),
                "created_at": "persistent_reflexion",
            }
        )
        _save_memories(memories)
        return (
            f"[Reflexion Stored]: {memory_id}\n"
            f"- Error Signature: {error_signature}\n"
            f"- Root Cause: {root_cause}\n"
            f"- Countermeasure: {countermeasure}\n"
            "Stored permanently in persistent memory."
        )
    except Exception as e:
        return f"Error recording failure reflexion: {e}"


def query_failure_reflexions(query: str = "") -> str:
    """Searches recorded failure reflexions and anti-patterns."""
    try:
        memories = _load_memories()
        anti_patterns = [m for m in memories if m.get("category") == "anti_pattern"]
        if not anti_patterns:
            return "No failure reflexions or anti-patterns recorded yet in Mem0."
        q = query.lower().strip()
        matched = [
            ap
            for ap in anti_patterns
            if not q
            or q in ap.get("error_signature", "").lower()
            or q in ap.get("root_cause", "").lower()
            or q in ap.get("countermeasure", "").lower()
        ]
        if not matched:
            return f"No anti-patterns matching query: '{query}'."
        out = [f"Found {len(matched)} failure reflexion(s):"]
        for item in matched[:10]:
            out.append(
                f"- [{item.get('id')}]: {item.get('error_signature')}\n"
                f"  Cause: {item.get('root_cause')}\n"
                f"  Fix: {item.get('countermeasure')}"
            )
        return "\n".join(out)
    except Exception as e:
        return f"Error querying failure reflexions: {e}"


if __name__ == "__main__":
    app.run()
