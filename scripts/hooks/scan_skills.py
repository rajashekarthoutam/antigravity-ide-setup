#!/usr/bin/env python3
"""
NVIDIA SkillSpector Runner for Antigravity IDE & God-Mode Ecosystem.
Scans all configured skills and plugins for prompt injection, sensitive data exposure, and security risks.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    target_dir = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(Path.home() / ".gemini" / "config" / "skills")
    )
    target_path = Path(target_dir).resolve()

    if not target_path.exists():
        print(f"[!] Target skills directory not found: {target_path}")
        sys.exit(1)

    print(f"[*] Running NVIDIA SkillSpector scan on: {target_path}")

    # Check for skillspector in PATH
    skillspector_bin = shutil.which("skillspector")
    if not skillspector_bin:
        # Check uv tool shims
        uv_shim = (
            Path.home()
            / "scoop"
            / "persist"
            / "uv"
            / "tools"
            / "shims"
            / "skillspector.exe"
        )
        if uv_shim.exists():
            skillspector_bin = str(uv_shim)
        else:
            print("[!] 'skillspector' not found in PATH or uv tools.")
            print(
                "    Run: uv tool install git+https://github.com/NVIDIA/skillspector.git"
            )
            sys.exit(1)

    env = os.environ.copy()
    env["TERM"] = "dumb"

    cmd = [
        skillspector_bin,
        "scan",
        str(target_path),
        "--recursive",
        "--no-llm",
    ]

    try:
        proc = subprocess.run(cmd, env=env, check=False)
        sys.exit(proc.returncode)
    except Exception as e:
        print(f"[!] Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
