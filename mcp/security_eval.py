"""
Security Evaluation, SkillSpector Verification, Model Armor & Agent Cards for God-Mode MCP.

Pure helper module (no imports from `server` to avoid circular dependencies).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from infinite_context import count_tokens_safe, redact_secrets, resolve_home_dir

_BASE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BASE_DIR.parent if _BASE_DIR.name == "mcp" else _BASE_DIR

_DUMMY_SECRET_RE = re.compile(
    r"['\"](?:mysecretpassword|changeme|placeholder|example[_-]?secret|your[_-]?(?:api[_-]?key|token|password|secret))['\"]",
    re.IGNORECASE,
)


def _resolve_skill_roots() -> list[Path]:
    """Locate skill directories across active workspace, config/skills, and config/skills_vault."""
    home_cfg = resolve_home_dir() / "config"
    candidates = [
        home_cfg / "skills",
        home_cfg / "skills_vault",
    ]
    if not os.environ.get("GOD_MODE_HOME", "").strip():
        candidates.insert(0, _REPO_ROOT / "skills")
    else:
        # When GOD_MODE_HOME is isolated in tests, still allow repo catalog lookup last
        candidates.append(_REPO_ROOT / "skills")

    roots: list[Path] = []
    for d in candidates:
        try:
            resolved = d.resolve()
            if resolved.exists() and resolved not in roots:
                roots.append(resolved)
        except OSError:
            continue
    return roots


def audit_agent_safety(target_path: str = ".") -> dict[str, Any]:
    """
    Automated safety audit scanning agent prompts, skills, scripts, and MCP tools
    for prompt injections, arbitrary code execution, and hardcoded credentials.
    """
    base = Path(target_path).resolve()
    findings: list[dict[str, Any]] = []
    scanned_count = 0

    dangerous_patterns = [
        (
            re.compile(r"\bInvoke-Expression\b|\biex\s+", re.IGNORECASE),
            "HIGH",
            "Dynamic PowerShell execution (Invoke-Expression) detected.",
        ),
        (
            re.compile(r"(?<!\.)\b(?:eval|exec)\s*\(", re.IGNORECASE),
            "HIGH",
            "Arbitrary code execution primitive (eval/exec) detected.",
        ),
        (
            re.compile(
                r"(?:api[_-]?key|secret|password|bearer|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
                re.IGNORECASE,
            ),
            "CRITICAL",
            "Hardcoded credential or token detected.",
        ),
        (
            re.compile(
                r"(?:rm\s+-rf\s+(?:~/?(?:\s|$|['\"*])|/(?:\s|$|\*|(?:etc|usr|var|home|root|bin|sbin|lib|boot|sys|dev|opt)\b))|del\s+/f\s+/s\s+/q\s+[A-Za-z]:\\)",
                re.IGNORECASE,
            ),
            "CRITICAL",
            "Destructive global filesystem wipe command detected.",
        ),
        (
            re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
            "HIGH",
            "Potential prompt injection phrase detected.",
        ),
    ]

    ignored_dirs = {".git", "node_modules", "target", ".venv", "venv", "__pycache__"}
    scan_exts = {
        ".md",
        ".py",
        ".js",
        ".ts",
        ".mjs",
        ".cjs",
        ".rb",
        ".json",
        ".ps1",
        ".cmd",
        ".bat",
        ".sh",
        ".yaml",
        ".yml",
    }

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() not in scan_exts:
                continue
            scanned_count += 1
            rel_path = str(p.relative_to(base)).replace("\\", "/")
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                is_md = p.suffix.lower() == ".md"
                for pattern, severity, msg in dangerous_patterns:
                    m = pattern.search(text)
                    if m:
                        line_no = text[: m.start()].count("\n") + 1
                        line_text = text.splitlines()[line_no - 1]
                        if (
                            is_md
                            and severity == "CRITICAL"
                            and "credential" in msg.lower()
                            and _DUMMY_SECRET_RE.search(line_text)
                            and re.search(
                                r"#\s*(?:NEVER|BAD|EXAMPLE)\b", line_text, re.IGNORECASE
                            )
                        ):
                            continue
                        findings.append(
                            {
                                "file": rel_path,
                                "line": line_no,
                                "severity": severity,
                                "description": msg,
                                "matched_sample": m.group(0)[:50],
                            }
                        )
            except Exception:
                continue

    crit_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in findings if f["severity"] == "HIGH")
    score = max(0, 100 - (crit_count * 30 + high_count * 15))
    status = "SAFE" if score >= 90 else ("WARNING" if score >= 60 else "CRITICAL")
    return {
        "status": status,
        "safety_score": score,
        "files_scanned": scanned_count,
        "total_findings": len(findings),
        "critical_issues": crit_count,
        "high_issues": high_count,
        "findings": findings[:20],
    }


def validate_a2a_handoff(
    sender: str,
    recipient: str,
    task_id: str,
    intent: str,
    scope: list[str],
    validators: list[str],
) -> dict[str, Any]:
    """Validates an Agent-to-Agent (A2A) Swarm task handoff envelope."""
    errors = []
    if not sender or not sender.strip():
        errors.append("Handoff missing required 'sender' identity.")
    if not recipient or not recipient.strip():
        errors.append("Handoff missing required 'recipient' identity.")
    if not task_id or not task_id.strip():
        errors.append("Handoff missing required 'task_id'.")
    if not intent or len(intent.strip()) < 5:
        errors.append(
            "Handoff 'intent' must be a specific descriptive goal (>= 5 chars)."
        )
    if not scope:
        errors.append("Handoff 'scope' must declare explicit path boundaries.")
    if not validators:
        errors.append(
            "Handoff 'validators' must define at least one deterministic verification command."
        )

    envelope = {
        "protocol": "A2A-1.0-Google-Antigravity",
        "sender": sender.strip(),
        "recipient": recipient.strip(),
        "task_id": task_id.strip(),
        "intent": intent.strip(),
        "scope": scope,
        "validators": validators,
        "valid": len(errors) == 0,
        "errors": errors,
    }
    raw_token = f"{sender}->{recipient}:{task_id}:{intent}"
    envelope["handoff_token"] = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()[
        :16
    ]
    return envelope


def verify_agent_skill(skill_path_or_url: str) -> dict[str, Any]:
    """
    SkillSpector AI skill security validator.
    Inspects SKILL.md, scripts (.py, .js, .ts, .mjs, .cjs, .rb, .sh, .ps1, etc.),
    and schemas for prompt injections, remote-pipe shell RCE, tool poisoning,
    method-free eval/exec, memory tampering, and credential leaks.
    """
    target = Path(skill_path_or_url).resolve()
    if not target.exists():
        return {
            "error": f"Target skill path does not exist: {skill_path_or_url}",
            "status": "ERROR",
        }

    scanned_files: list[Path] = []
    if target.is_file():
        scanned_files.append(target)
    else:
        for root, _, files in os.walk(target):
            for f in files:
                scanned_files.append(Path(root) / f)

    signatures = [
        (
            re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
            "CRITICAL",
            "Prompt Injection: Instruction override directive detected.",
        ),
        (
            re.compile(
                r"(?:system\s+override|jailbreak|disregard\s+prior\s+guidelines)",
                re.IGNORECASE,
            ),
            "CRITICAL",
            "Prompt Injection: System prompt evasion phrase detected.",
        ),
        (
            re.compile(
                r"[\u200B\u200C\uFEFF]|(?<![\U0001F300-\U0001FAFF\u2600-\u27BF])\u200D|\u200D(?![\U0001F300-\U0001FAFF\u2600-\u27BF])",
                re.UNICODE,
            ),
            "CRITICAL",
            "Stealth Exploit: Zero-width Unicode characters detected (hidden instruction vector).",
        ),
        (
            re.compile(r"\bInvoke-Expression\b|\biex\s+", re.IGNORECASE),
            "HIGH",
            "Arbitrary Execution: PowerShell Invoke-Expression detected.",
        ),
        (
            re.compile(r"(?<!\.)\b(?:eval|exec)\s*\(", re.IGNORECASE),
            "HIGH",
            "Arbitrary Execution: Dynamic code execution (eval/exec) detected.",
        ),
        (
            re.compile(r"curl\s+(?!\.\.\.\s*\|)[^\n]*?\|\s*(?:ba)?sh\b", re.IGNORECASE),
            "CRITICAL",
            "Malicious Pipeline: Remote script piped directly to shell.",
        ),
        (
            re.compile(r"\b(?:downloadstring|downloadfile)\s*\(", re.IGNORECASE),
            "HIGH",
            "Unsafe Network: Direct web payload download method detected.",
        ),
        (
            re.compile(
                r"(?:api[_-]?key|secret|password|bearer|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
                re.IGNORECASE,
            ),
            "CRITICAL",
            "Credential Risk: Hardcoded API key or token detected.",
        ),
        (
            re.compile(r"(?:cat|type|Get-Content)\s+.*?\.ssh[/\\]", re.IGNORECASE),
            "CRITICAL",
            "Exfiltration Hazard: Tool attempts reading SSH private credentials.",
        ),
        (
            re.compile(r"env\s*:\s*[A-Z_]+.*?webhook|webhook.*?env\s*:", re.IGNORECASE),
            "CRITICAL",
            "Exfiltration Hazard: Environment variables routed to external webhook.",
        ),
        (
            re.compile(
                r"(?:rm\s+-rf\s+(?:~/?(?:\s|$|['\"*])|/(?:\s|$|\*|(?:etc|usr|var|home|root|bin|sbin|lib|boot|sys|dev|opt)\b))|del\s+/f\s+/s\s+/q\s+[A-Za-z]:\\)",
                re.IGNORECASE,
            ),
            "CRITICAL",
            "Destructive Payload: Global filesystem wipe command detected.",
        ),
        (
            re.compile(
                r"(?:memory\.json|god_mode_mem0\.json).*?overwrite|overwrite.*?(?:memory\.json|god_mode_mem0)",
                re.IGNORECASE,
            ),
            "HIGH",
            "Memory Poisoning: Attempt to overwrite persistent memory store.",
        ),
    ]

    scan_exts = {
        ".md",
        ".py",
        ".js",
        ".ts",
        ".mjs",
        ".cjs",
        ".rb",
        ".json",
        ".ps1",
        ".cmd",
        ".bat",
        ".sh",
        ".yaml",
        ".yml",
        ".txt",
    }

    findings: list[dict[str, Any]] = []
    for p in scanned_files:
        if p.suffix.lower() not in scan_exts:
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        is_md = p.suffix.lower() == ".md"
        rel_name = (
            p.name
            if target.is_file()
            else str(p.relative_to(target)).replace("\\", "/")
        )
        lines = content.splitlines()

        for pattern, severity, msg in signatures:
            for idx, line in enumerate(lines, start=1):
                m = pattern.search(line)
                if m:
                    if (
                        is_md
                        and severity == "CRITICAL"
                        and "Credential Risk" in msg
                        and _DUMMY_SECRET_RE.search(line)
                        and re.search(
                            r"#\s*(?:NEVER|BAD|EXAMPLE)\b", line, re.IGNORECASE
                        )
                    ):
                        continue
                    findings.append(
                        {
                            "file": rel_name,
                            "line": idx,
                            "severity": severity,
                            "issue": msg,
                            "snippet": line.strip()[:100],
                        }
                    )

    crit = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high = sum(1 for f in findings if f["severity"] == "HIGH")
    trust_score = max(0, 100 - (crit * 35 + high * 15))

    if trust_score >= 85 and crit == 0:
        verdict = "VERIFIED_SAFE"
        verdict_summary = "Skill passed SkillSpector security validation. Zero malicious patterns detected."
    elif trust_score >= 50 and crit == 0:
        verdict = "WARNING_FLAGGED"
        verdict_summary = f"Skill flagged with {len(findings)} potential security concerns. Review before install."
    else:
        verdict = "MALICIOUS_REJECTED"
        verdict_summary = (
            f"CRITICAL: Skill rejected. Found {crit} critical exploit vector(s)."
        )

    return {
        "verdict": verdict,
        "trust_score": trust_score,
        "summary": verdict_summary,
        "files_scanned": len(scanned_files),
        "total_findings": len(findings),
        "critical_count": crit,
        "high_count": high,
        "findings": findings[:25],
    }


def model_armor_sanitize(text: str, direction: str = "output") -> dict[str, Any]:
    """
    Google Model Armor-inspired LLM firewall and runtime guardrail.
    Redacts credentials, tokens, and private keys and inspects inputs for prompt injections.
    """
    sanitized = redact_secrets(text)
    redactions = 1 if sanitized != text else 0

    is_safe = True
    security_alerts: list[str] = []
    if direction == "input":
        injection_patterns = [
            (
                re.compile(
                    r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE
                ),
                "Direct prompt injection attempt detected.",
            ),
            (
                re.compile(r"[\u200B-\u200D\uFEFF]", re.UNICODE),
                "Invisible zero-width Unicode injection detected.",
            ),
        ]
        for pat, alert in injection_patterns:
            if pat.search(text):
                is_safe = False
                security_alerts.append(alert)

    return {
        "direction": direction,
        "is_safe": is_safe,
        "redactions_applied": redactions,
        "sanitized_text": sanitized,
        "security_alerts": security_alerts,
    }


def get_agent_card(agent_name: str) -> dict[str, Any]:
    """Returns Google A2A AgentCard metadata specification for an AI agent role."""
    cards: dict[str, dict[str, Any]] = {
        "self": {
            "schema_version": "a2a-v1.0",
            "agent_id": "self",
            "display_name": "Full Capability Agent Clone",
            "description": "Subagent inheriting full configuration, tools, and execution model.",
            "capabilities": [
                "code_editing",
                "command_execution",
                "ast_inspection",
                "memory_store",
                "validation",
            ],
            "sandbox_mode": "full_execution",
            "network_access": True,
            "max_context_budget": 64000,
            "supported_protocols": ["A2A-1.0-Google-Antigravity"],
        },
        "research": {
            "schema_version": "a2a-v1.0",
            "agent_id": "research",
            "display_name": "Codebase & Web Researcher",
            "description": "Read-only exploration subagent for codebase surveys and file inspection.",
            "capabilities": ["code_search", "web_search", "file_read"],
            "sandbox_mode": "read_only",
            "network_access": False,
            "max_context_budget": 32000,
            "supported_protocols": ["A2A-1.0-Google-Antigravity"],
        },
        "browser": {
            "schema_version": "a2a-v1.0",
            "agent_id": "browser",
            "display_name": "Multimodal Browser Automation Agent",
            "description": "Drives Chrome DevTools for live web page navigation and testing.",
            "capabilities": [
                "browser_navigation",
                "form_fill",
                "screenshot_inspection",
                "dom_interaction",
            ],
            "sandbox_mode": "browser_sandbox",
            "network_access": True,
            "max_context_budget": 32000,
            "supported_protocols": ["A2A-1.0-Google-Antigravity"],
        },
        "security-auditor": {
            "schema_version": "a2a-v1.0",
            "agent_id": "security-auditor",
            "display_name": "SkillSpector & NeMo Security Auditor",
            "description": "Audits agent skills, prompts, MCP configs, and tool pipelines.",
            "capabilities": [
                "skill_verification",
                "prompt_injection_scan",
                "secret_leak_check",
                "mcp_audit",
            ],
            "sandbox_mode": "read_only",
            "network_access": False,
            "max_context_budget": 32000,
            "supported_protocols": ["A2A-1.0-Google-Antigravity"],
        },
    }
    key = agent_name.lower().strip()
    if key in cards:
        return cards[key]
    return {
        "schema_version": "a2a-v1.0",
        "agent_id": agent_name,
        "display_name": f"{agent_name.capitalize()} Agent",
        "description": "Custom autonomous worker in the Antigravity swarm.",
        "capabilities": ["custom_execution"],
        "sandbox_mode": "standard",
        "network_access": False,
        "max_context_budget": 32000,
        "supported_protocols": ["A2A-1.0-Google-Antigravity"],
    }


def list_agent_cards() -> list[dict[str, Any]]:
    """Lists all registered Google A2A AgentCard specifications."""
    return [
        get_agent_card(r) for r in ("self", "research", "browser", "security-auditor")
    ]


def synthesize_skill(name: str, description: str, instructions: str) -> str:
    """
    Generates and registers a new on-demand skill with validated YAML frontmatter.
    Writes to active config skills directory (and workspace skills/ when not isolated).
    """
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "-", name).strip("-").lower()
    if not clean_name:
        return "Error: Invalid skill name."

    content = (
        f"---\nname: {clean_name}\ndescription: {description.strip()}\n---\n\n"
        f"{instructions.strip()}\n"
    )
    target_paths = [resolve_home_dir() / "config" / "skills" / clean_name / "SKILL.md"]
    if not os.environ.get("GOD_MODE_HOME", "").strip():
        target_paths.append(
            _REPO_ROOT / "skills" / "ai-agentic" / clean_name / "SKILL.md"
        )

    saved: list[str] = []
    for p in target_paths:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            saved.append(str(p))
        except OSError:
            continue

    return (
        f"[Creator Mode] Skill '{clean_name}' synthesized successfully.\nRegistered at:\n- "
        + "\n- ".join(saved)
    )


def search_skills(query: str, limit: int = 5) -> str:
    """
    Searches active `skills/` and `skills_vault/` libraries on demand so domain
    expertise stays out of the baseline system prompt until needed.
    """
    vault_dirs = _resolve_skill_roots()
    matches: list[tuple[int, str, str, str]] = []
    seen_names: set[str] = set()
    q_terms = [t.lower() for t in query.split() if t.strip()]

    for vdir in vault_dirs:
        for skill_file in vdir.rglob("SKILL.md"):
            skill_path = skill_file.parent
            sname = skill_path.name
            if sname.lower() in seen_names:
                continue
            seen_names.add(sname.lower())
            name = sname.lower()
            score = 0
            desc = ""
            try:
                head = skill_file.read_text(encoding="utf-8", errors="ignore")[:1000]
                for term in q_terms:
                    if term in name:
                        score += 3
                    if term in head.lower():
                        score += 1
                m = re.search(r"description:\s*(.+)", head)
                if m:
                    desc = m.group(1).strip().strip("'\"")
            except Exception:
                pass
            if score > 0 or not q_terms:
                matches.append((score, sname, desc, str(skill_file.resolve())))

    matches.sort(key=lambda x: x[0], reverse=True)
    selected = matches[:limit]
    if not selected:
        return f"No matching skills found in vault for query: '{query}'."

    out = [f"Found {len(selected)} skill(s) in vault for '{query}':"]
    for _, sname, sdesc, spath in selected:
        out.append(f"- **{sname}**: {sdesc}\n  Path: {spath}")
    return "\n".join(out)


def evaluate_skill(skill_path_or_name: str) -> dict[str, Any]:
    """
    Deterministic Skill Evaluator across 5 engineering dimensions:
    frontmatter (25), token economy (25), actionability (20), security (20), structure (10).
    """
    candidate = Path(skill_path_or_name)
    if not candidate.exists():
        found: list[Path] = []
        for sroot in _resolve_skill_roots():
            found = list(sroot.rglob(f"{skill_path_or_name}/SKILL.md"))
            if found:
                break
        if not found:
            return {
                "status": "ERROR",
                "error": f"Skill not found: {skill_path_or_name}",
            }
        skill_md = found[0]
        skill_dir = skill_md.parent
    elif candidate.is_dir():
        skill_dir = candidate
        skill_md = candidate / "SKILL.md"
    else:
        skill_md = candidate
        skill_dir = candidate.parent

    if not skill_md.exists():
        return {"status": "ERROR", "error": f"SKILL.md missing in {skill_dir}"}

    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    token_count = count_tokens_safe(content)
    recommendations: list[str] = []

    fm_score = 0
    has_fm = content.startswith("---") and "---" in content[3:]
    if has_fm:
        fm_score += 10
        fm_block = content.split("---", 2)[1]
        if re.search(r"(?m)^name:\s*\S+", fm_block):
            fm_score += 5
        else:
            recommendations.append("Add 'name:' field to YAML frontmatter.")
        desc_match = re.search(r"(?m)^description:\s*(.+)", fm_block)
        if desc_match and len(desc_match.group(1).strip()) >= 20:
            fm_score += 5
        if re.search(
            r"\b(when|use\s+when|trigger|always|before)\b", fm_block, re.IGNORECASE
        ):
            fm_score += 5
        else:
            recommendations.append(
                "Clarify explicit 'Use when...' trigger conditions in description."
            )
    else:
        recommendations.append(
            "Add valid YAML frontmatter (--- name / description ---)."
        )

    has_refs = (skill_dir / "references").exists() or (skill_dir / "scripts").exists()
    if token_count <= 1500:
        tok_score = 25
    elif token_count <= 3000:
        tok_score = 20 if has_refs else 15
        if not has_refs:
            recommendations.append(
                "Offload bulky examples/docs to references/ or scripts/."
            )
    elif token_count <= 5000:
        tok_score = 12
        recommendations.append(
            f"SKILL.md is {token_count} tokens; trim or split into references/."
        )
    else:
        tok_score = 5
        recommendations.append(
            f"SKILL.md bloats context ({token_count} tokens). Refactor for progressive disclosure."
        )

    act_score = 0
    if re.search(
        r"(?i)\b(verif|test|check|assert|lint|validate|exit\s*code)\b", content
    ):
        act_score += 10
    else:
        recommendations.append("Add deterministic verification/validation steps.")
    if "```" in content or re.search(r"(?m)^\s*\d+\.\s+", content):
        act_score += 10
    else:
        recommendations.append("Include concrete numbered steps or command blocks.")

    sec_report = verify_agent_skill(str(skill_dir))
    sec_status = sec_report.get("verdict", sec_report.get("status", "UNKNOWN"))
    if sec_status in {"VERIFIED_SAFE", "PASS"}:
        sec_score = 20
    elif sec_status in {"WARN", "CAUTION", "WARNING_FLAGGED"}:
        sec_score = 12
        recommendations.append(
            "Resolve security warnings flagged by verify_agent_skill."
        )
    else:
        sec_score = 0
        recommendations.append(
            "CRITICAL: Resolve security findings flagged by verify_agent_skill."
        )

    struct_score = (
        10 if (len(lines) >= 15 and re.search(r"(?m)^##?\s+", content)) else 5
    )

    total_score = fm_score + tok_score + act_score + sec_score + struct_score
    grade = (
        "A"
        if total_score >= 90
        else "B"
        if total_score >= 80
        else "C"
        if total_score >= 70
        else "D"
        if total_score >= 60
        else "F"
    )

    try:
        rel_out = str(skill_md.resolve().relative_to(_REPO_ROOT.resolve())).replace(
            "\\", "/"
        )
    except ValueError:
        rel_out = str(skill_md)

    return {
        "skill": skill_dir.name,
        "path": rel_out,
        "score": total_score,
        "grade": grade,
        "token_count": token_count,
        "breakdown": {
            "frontmatter_and_triggers": f"{fm_score}/25",
            "token_economy": f"{tok_score}/25",
            "actionability_and_verification": f"{act_score}/20",
            "security_safety": f"{sec_score}/20",
            "structure": f"{struct_score}/10",
        },
        "security_status": sec_status,
        "recommendations": recommendations,
    }
