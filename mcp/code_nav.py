"""
Code Navigation, AST Inspection, Impact Graph & Read Guardrails for God-Mode MCP.

Pure helper module (no imports from `server` to avoid circular dependencies).
"""

from __future__ import annotations

import ast
import difflib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from infinite_context import count_tokens_safe

DIFFT_BIN = Path(
    shutil.which("difft")
    or (
        Path.home()
        / "AppData"
        / "Local"
        / "headroom"
        / "bin"
        / "difft-0.64.0-windows-x86_64"
        / "difft.exe"
    )
)
SCC_BIN = Path(
    shutil.which("scc")
    or (
        Path.home()
        / "AppData"
        / "Local"
        / "headroom"
        / "bin"
        / "scc-3.5.0-windows-x86_64"
        / "scc.exe"
    )
)

# In-memory session cache for diff-only re-reads
_SESSION_FILE_CACHE: dict[str, str] = {}

_CODE_EXTS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".rs",
    ".go",
    ".java",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
}
_SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "target",
    "__pycache__",
    ".agents",
    "bin",
    "obj",
    ".idea",
    ".vscode",
}


def github_agentic_probe(
    query_type: str = "status", repo: str = "", limit: int = 5
) -> str:
    """
    Ultra-lean GitHub CLI integration for agentic workflows.
    Queries PRs, issues, CI workflow runs, or repo status (< 150 tokens).
    """
    gh_bin = shutil.which("gh")
    if not gh_bin:
        return "GitHub CLI ('gh') is not installed or not in PATH."

    try:
        repo_args = ["-R", repo] if repo else []
        if query_type == "prs":
            cmd = [gh_bin, "pr", "list", "--limit", str(limit)] + repo_args
        elif query_type == "issues":
            cmd = [gh_bin, "issue", "list", "--limit", str(limit)] + repo_args
        elif query_type == "runs":
            cmd = [gh_bin, "run", "list", "--limit", str(limit)] + repo_args
        else:
            cmd = (
                [gh_bin, "repo", "view"]
                + repo_args
                + [
                    "--json",
                    "name,description,defaultBranchRef,visibility",
                    "--template",
                    "{{.name}} ({{.visibility}}): {{.description}}\nDefault Branch: {{.defaultBranchRef.name}}",
                ]
            )

        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        if res.returncode != 0:
            return f"[gh error]: {err or out}"
        return out or "No items found."
    except Exception as e:
        return f"[gh error]: {e}"


def code_reference_probe(symbol: str, root_dir: str = ".") -> str:
    """
    Finds structural definitions, call sites, and usages of a symbol across code files
    using Tree-sitter (`ast-grep`) with fast Python fallback (< 150 tokens).
    """
    try:
        hits: list[str] = []
        ast_grep_bin = shutil.which("ast-grep")
        if ast_grep_bin:
            globs = [
                "--globs",
                "!*.md",
                "--globs",
                "!**/.git/**",
                "--globs",
                "!**/brain/**",
                "--globs",
                "!**/node_modules/**",
            ]
            for pattern in (f"{symbol}($...)", symbol):
                if hits:
                    break
                cmd = [ast_grep_bin, "run", "--pattern", pattern, "--json=stream"]
                res = subprocess.run(
                    cmd + globs + [root_dir],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=8,
                )
                for line in res.stdout.strip().splitlines()[:10]:
                    try:
                        d = json.loads(line)
                        fp = d.get("file", "")
                        r = d.get("range", {}).get("start", {}).get("line", "?")
                        txt = d.get("text", "").strip().splitlines()[0][:70]
                        hits.append(f"  {fp}:{r} -> {txt}")
                    except Exception:
                        continue

        if not hits:
            sym_re = re.compile(rf"\b{re.escape(symbol)}\b")
            base = Path(root_dir).resolve()
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
                for fn in filenames:
                    p = Path(dirpath) / fn
                    if p.suffix.lower() not in _CODE_EXTS:
                        continue
                    rel = str(p.relative_to(base)).replace("\\", "/")
                    for idx, line in enumerate(
                        p.read_text(encoding="utf-8", errors="ignore").splitlines(),
                        start=1,
                    ):
                        if sym_re.search(line):
                            hits.append(f"  {rel}:{idx} -> {line.strip()[:70]}")
                            if len(hits) >= 8:
                                break
                    if len(hits) >= 8:
                        break
                if len(hits) >= 8:
                    break

        if hits:
            return f"# References for '{symbol}':\n" + "\n".join(hits[:8])
        return f"No AST references found for symbol '{symbol}'."
    except Exception as e:
        return f"Error probing symbol '{symbol}': {e}"


def safe_read_file(
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    max_lines: int = 100,
) -> str:
    """
    Enforces strict anti-waste reading guardrails.
    Blocks whole files over max_lines (default 100) unless sliced.
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        return f"File does not exist: {path}"

    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        if start_line is None and end_line is None:
            if total_lines > max_lines:
                return (
                    f"[READ BLOCKED by token guardrail]: {path} has {total_lines} lines (> {max_lines} line threshold).\n"
                    "-> Use 'get_file_outline' to inspect symbol signatures (~80 tokens).\n"
                    "-> Or specify start_line and end_line to read a targeted window."
                )
            _SESSION_FILE_CACHE[str(p.resolve())] = "\n".join(lines)
            return "\n".join(lines)

        s = max(1, start_line or 1) - 1
        e = min(total_lines, end_line or total_lines)
        sliced = lines[s:e]
        return f"// {path} | Lines {s + 1}-{e} of {total_lines}\n" + "\n".join(sliced)
    except Exception as e:
        return f"Error reading file: {e}"


def diff_re_read(path: str) -> str:
    """
    Diff-Only Re-Read: returns only unified delta lines since last read in this session.
    """
    p = Path(path).resolve()
    key = str(p)
    if not p.exists() or not p.is_file():
        return f"File not found: {path}"

    current_content = p.read_text(encoding="utf-8", errors="replace")

    if key not in _SESSION_FILE_CACHE:
        _SESSION_FILE_CACHE[key] = current_content
        lines = current_content.splitlines()
        if len(lines) > 100:
            return (
                f"[Initial read cached. File exceeds 100 lines ({len(lines)} lines)].\n"
                "Subsequent reads will produce diffs only. Use get_file_outline for symbol definitions."
            )
        return current_content

    prev_content = _SESSION_FILE_CACHE[key]
    if prev_content == current_content:
        return f"[DIFF-CACHE HIT]: {path} is UNMODIFIED since last read. (0 tokens consumed)"

    diff = list(
        difflib.unified_diff(
            prev_content.splitlines(keepends=True),
            current_content.splitlines(keepends=True),
            fromfile=f"{path} (cached)",
            tofile=f"{path} (current)",
            n=3,
        )
    )
    _SESSION_FILE_CACHE[key] = current_content
    return f"[DIFF DELTA ONLY - {len(diff)} diff lines]:\n" + "".join(diff)


def _python_outline_items(fp: Path) -> list[dict[str, Any]]:
    """Fast pure-Python AST outline extractor avoiding per-file subprocess overhead."""
    try:
        src = fp.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(fp))
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            if isinstance(node, ast.ClassDef):
                sig = f"class {node.name}"
            else:
                args = [a.arg for a in node.args.args]
                prefix = (
                    "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                )
                sig = f"{prefix}{node.name}({', '.join(args[:6])})"
            items.append(
                {
                    "name": node.name,
                    "symbolType": kind,
                    "signature": sig,
                    "range": {
                        "start": {"line": max(0, node.lineno - 1)},
                        "end": {"line": max(0, (node.end_lineno or node.lineno) - 1)},
                    },
                }
            )
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        s_args = [a.arg for a in sub.args.args]
                        items.append(
                            {
                                "name": sub.name,
                                "symbolType": "method",
                                "signature": f"def {node.name}.{sub.name}({', '.join(s_args[:5])})",
                                "range": {
                                    "start": {"line": max(0, sub.lineno - 1)},
                                    "end": {
                                        "line": max(
                                            0, (sub.end_lineno or sub.lineno) - 1
                                        )
                                    },
                                },
                            }
                        )
    return items


def _run_pagerank(
    graph: dict[str, list[str]], damping: float = 0.85, iterations: int = 20
) -> dict[str, float]:
    nodes = list(graph.keys())
    if not nodes:
        return {}
    n = len(nodes)
    ranks = {node: 1.0 / n for node in nodes}
    for _ in range(iterations):
        new_ranks = {node: (1.0 - damping) / n for node in nodes}
        for node, edges in graph.items():
            if edges:
                share = (damping * ranks[node]) / len(edges)
                for neighbor in edges:
                    if neighbor in new_ranks:
                        new_ranks[neighbor] += share
            else:
                for other in nodes:
                    new_ranks[other] += (damping * ranks[node]) / n
        ranks = new_ranks
    return ranks


def pagerank_repo_map(root_dir: str = ".", max_tokens: int = 1024) -> str:
    """
    Constructs an Aider-style AST repository map using PageRank, packed into
    a strict token budget (default 1,024 tokens).
    """
    root = Path(root_dir).resolve()
    file_map: dict[str, Path] = {}
    graph: dict[str, list[str]] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for f in filenames:
            fp = Path(dirpath) / f
            if fp.suffix.lower() in _CODE_EXTS:
                rel = str(fp.relative_to(root)).replace("\\", "/")
                file_map[rel] = fp
                graph[rel] = []

    if not file_map:
        return f"No matching source code files found in {root_dir}."

    ast_grep_bin = shutil.which("ast-grep")
    file_signatures: dict[str, list[str]] = {}
    for rel, fp in file_map.items():
        try:
            sigs: list[str] = []
            if fp.suffix.lower() == ".py":
                sigs = [it["signature"] for it in _python_outline_items(fp)]
            elif ast_grep_bin:
                res = subprocess.run(
                    [ast_grep_bin, "outline", "--json=stream", str(fp)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=6,
                )
                for line in res.stdout.strip().splitlines():
                    try:
                        d = json.loads(line)
                        for it in d.get("items", []):
                            sym = it.get("signature") or it.get("name")
                            if sym:
                                sigs.append(sym)
                    except Exception:
                        continue
            file_signatures[rel] = sigs
            content = fp.read_text(encoding="utf-8", errors="ignore").lower()
            for other_rel in file_map:
                if other_rel != rel:
                    stem = Path(other_rel).stem.lower()
                    if stem in content:
                        graph[rel].append(other_rel)
        except Exception:
            continue

    ranks = _run_pagerank(graph)
    sorted_files = sorted(ranks.items(), key=lambda x: x[1], reverse=True)

    header = f"# PageRank Architecture Map (Budget: {max_tokens} tokens)\n\n"
    output_chunks = [header]
    current_tokens = count_tokens_safe(header)

    for rel, score in sorted_files:
        sigs = file_signatures.get(rel, [])
        if not sigs:
            continue
        chunk = (
            f"### {rel} (Rank: {score:.3f})\n"
            + "\n".join(f"  {s}" for s in sigs[:8])
            + "\n\n"
        )
        chunk_tokens = count_tokens_safe(chunk)
        if current_tokens + chunk_tokens > max_tokens:
            output_chunks.append(f"... [Truncated at {max_tokens} token cap]")
            break
        output_chunks.append(chunk)
        current_tokens += chunk_tokens

    return "".join(output_chunks)


def get_file_outline(path: str) -> str:
    """Parses a source file into a structural symbol outline."""
    fp = Path(path)
    if not fp.exists() or not fp.is_file():
        return f"No symbols extracted or file not found: {path}"
    try:
        if fp.suffix.lower() == ".py":
            items = _python_outline_items(fp)
            if items:
                lines = [f"File: {path} (python)"]
                for it in items:
                    r = it["range"]
                    lines.append(
                        f"  [{it['symbolType'].upper()}] {it['name']} "
                        f"(lines {r['start']['line'] + 1}-{r['end']['line'] + 1}): {it['signature']}"
                    )
                return "\n".join(lines)

        ast_grep_bin = shutil.which("ast-grep")
        if not ast_grep_bin:
            return "No structural symbols found."
        result = subprocess.run(
            [ast_grep_bin, "outline", "--json=stream", path],
            capture_output=True,
            text=True,
            check=False,
        )
        if not result.stdout.strip():
            return f"No symbols extracted or file not found: {path}"

        lines = []
        for line in result.stdout.strip().splitlines():
            try:
                data = json.loads(line)
                lines.append(f"File: {data.get('path')} ({data.get('language')})")
                for it in data.get("items", []):
                    r = it.get("range", {})
                    start_l = r.get("start", {}).get("line", "?")
                    end_l = r.get("end", {}).get("line", "?")
                    sym_type = it.get("symbolType", "symbol")
                    name = it.get("name", "anonymous")
                    sig = it.get("signature", name)
                    lines.append(
                        f"  [{sym_type.upper()}] {name} (lines {start_l}-{end_l}): {sig}"
                    )
            except Exception:
                continue
        return "\n".join(lines) if lines else "No structural symbols found."
    except Exception as e:
        return f"Error extracting outline: {e}"


def get_symbol(path: str, symbol_name: str) -> str:
    """Extracts ONLY the definition and body of a specific function, class, or method."""
    fp = Path(path)
    if not fp.exists() or not fp.is_file():
        return f"Could not parse file: {path}"
    try:
        target_item: dict[str, Any] | None = None
        if fp.suffix.lower() == ".py":
            for it in _python_outline_items(fp):
                if it["name"].lower() == symbol_name.lower():
                    target_item = it
                    break

        if not target_item:
            ast_grep_bin = shutil.which("ast-grep")
            if ast_grep_bin:
                result = subprocess.run(
                    [ast_grep_bin, "outline", "--json=stream", path],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                for line in result.stdout.strip().splitlines():
                    try:
                        data = json.loads(line)
                        for it in data.get("items", []):
                            if it.get("name", "").lower() == symbol_name.lower():
                                target_item = it
                                break
                        if target_item:
                            break
                    except Exception:
                        continue

        if not target_item:
            return f"Symbol '{symbol_name}' not found in {path}."

        r = target_item.get("range", {})
        start_line = int(r.get("start", {}).get("line", 0))
        end_line = int(r.get("end", {}).get("line", start_line))

        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        start_idx = max(0, start_line)
        end_idx = min(len(all_lines), end_line + 1)
        selected_code = "".join(all_lines[start_idx:end_idx])
        return (
            f"// Symbol: {symbol_name} ({target_item.get('symbolType', 'item')}) "
            f"| Lines {start_idx + 1}-{end_idx}\n{selected_code}"
        )
    except Exception as e:
        return f"Error retrieving symbol: {e}"


def repo_shape_probe(target_path: str = ".") -> str:
    """Probes project language distribution, file counts, and lines of code."""
    if SCC_BIN.exists():
        try:
            res = subprocess.run(
                [str(SCC_BIN), target_path, "--format", "wide"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    counts: dict[str, dict[str, int]] = {}
    root = Path(target_path).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            fp = Path(dirpath) / fn
            ext = fp.suffix.lower() or "(no ext)"
            bucket = counts.setdefault(ext, {"files": 0, "lines": 0})
            bucket["files"] += 1
            try:
                bucket["lines"] += len(
                    fp.read_text(encoding="utf-8", errors="ignore").splitlines()
                )
            except OSError:
                continue
    rows = [
        f"{ext}: {stats['files']} files, {stats['lines']} lines"
        for ext, stats in sorted(
            counts.items(), key=lambda x: x[1]["lines"], reverse=True
        )[:15]
    ]
    return "\n".join(rows) if rows else "No files found."


def structural_diff(file_a: str, file_b: str) -> str:
    """Computes structural syntax tree diffs (or unified diff fallback)."""
    if DIFFT_BIN.exists():
        try:
            res = subprocess.run(
                [str(DIFFT_BIN), "--color", "never", file_a, file_b],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip() or "Files are structurally identical."
        except Exception:
            pass
    pa, pb = Path(file_a), Path(file_b)
    if not pa.exists() or not pb.exists():
        return f"File not found: {file_a if not pa.exists() else file_b}"
    diff = list(
        difflib.unified_diff(
            pa.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True),
            pb.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True),
            fromfile=file_a,
            tofile=file_b,
        )
    )
    return "".join(diff).strip() or "Files are identical."


def validate_syntax(code: str, lang: str = "python") -> dict[str, Any]:
    """Validates code syntax prior to editing to avoid broken-syntax token burns."""
    lang_lower = lang.lower()
    if "python" in lang_lower or lang_lower.endswith(".py"):
        try:
            ast.parse(code)
            return {"valid": True, "message": "Syntax valid."}
        except SyntaxError as se:
            return {
                "valid": False,
                "error": str(se),
                "line": se.lineno,
                "offset": se.offset,
            }
    try:
        ast_grep_bin = shutil.which("ast-grep")
        if not ast_grep_bin:
            return {"valid": True, "message": "Validation skipped: ast-grep absent."}
        res = subprocess.run(
            [ast_grep_bin, "scan", "--stdin", "--lang", lang_lower],
            input=code,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "valid": res.returncode == 0,
            "message": "AST scan passed" if res.returncode == 0 else res.stderr.strip(),
        }
    except Exception as e:
        return {"valid": True, "message": f"Validation skipped: {e}"}


def code_graph_impact_probe(symbol: str, root_dir: str = ".") -> str:
    """
    Two-pass AST code topology and blast-radius impact analyzer.
    Finds symbol definition, complete cross-file importers, and direct callers.
    """
    try:
        base = Path(root_dir).resolve()
        def_file: str | None = None
        def_line: int | None = None
        def_type = "unknown"
        callers: list[dict[str, Any]] = []
        impacted_tests: list[str] = []
        file_texts: dict[str, tuple[str, bool]] = {}

        def_regex = re.compile(
            rf"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function|class|interface|type|fn|def)\s+{re.escape(symbol)}\b",
            re.MULTILINE,
        )

        # Pass 1: discover definitions and cache normalized contents
        for root, dirs, files in sorted(os.walk(base)):
            dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
            for file in sorted(files):
                p = Path(root) / file
                if p.suffix.lower() not in _CODE_EXTS:
                    continue
                rel_path = str(p.relative_to(base)).replace("\\", "/")
                is_test = (
                    "test" in rel_path.lower()
                    or p.name.startswith("test_")
                    or p.name.endswith("_test.py")
                )
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                file_texts[rel_path] = (content, is_test)

                if p.suffix.lower() == ".py":
                    try:
                        tree = ast.parse(content, filename=str(p))
                        for node in ast.walk(tree):
                            if (
                                isinstance(
                                    node,
                                    (
                                        ast.FunctionDef,
                                        ast.AsyncFunctionDef,
                                        ast.ClassDef,
                                    ),
                                )
                                and node.name == symbol
                            ):
                                def_file = rel_path
                                def_line = node.lineno
                                def_type = (
                                    "class"
                                    if isinstance(node, ast.ClassDef)
                                    else "function"
                                )
                    except Exception:
                        pass

                if not def_file:
                    m = def_regex.search(content)
                    if m:
                        def_file = rel_path
                        def_line = content[: m.start()].count("\n") + 1
                        def_type = "symbol_definition"

        # Pass 2: collect all callers and importers accurately regardless of walk order
        call_regex = re.compile(rf"\b{re.escape(symbol)}\s*\(")
        importers: list[str] = []
        import_regex = None
        if def_file:
            def_mod = Path(def_file).stem
            import_regex = re.compile(
                rf"(?:import.*?\b{re.escape(def_mod)}\b|from.*?\b{re.escape(def_mod)}\b)"
            )

        for rel_path, (content, is_test) in file_texts.items():
            for idx, line in enumerate(content.splitlines(), start=1):
                if call_regex.search(line):
                    if def_file and rel_path == def_file and idx == def_line:
                        continue
                    callers.append(
                        {
                            "file": rel_path,
                            "line": idx,
                            "snippet": line.strip()[:100],
                        }
                    )
                    if is_test and rel_path not in impacted_tests:
                        impacted_tests.append(rel_path)
            if (
                import_regex
                and def_file
                and rel_path != def_file
                and import_regex.search(content)
                and rel_path not in importers
            ):
                importers.append(rel_path)

        distinct_caller_files = len({c["file"] for c in callers})
        if distinct_caller_files <= 1 and len(callers) <= 2:
            risk = "LOW"
        elif distinct_caller_files <= 3 and len(callers) <= 8:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        return json.dumps(
            {
                "symbol": symbol,
                "definition": {
                    "file": def_file or "not_found",
                    "line": def_line,
                    "type": def_type,
                },
                "blast_radius_risk": risk,
                "total_callers": len(callers),
                "impacted_files_count": distinct_caller_files,
                "impacted_test_files": impacted_tests,
                "importing_files": importers[:10],
                "direct_call_sites": callers[:15],
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})
