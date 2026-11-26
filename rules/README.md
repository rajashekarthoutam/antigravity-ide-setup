# Rules

## Structure

Rules are organized into a **common** layer plus **10 language/framework** directories (11 total rule directories):

```text
rules/
├── common/          # Universal invariants, token economy, testing, git, security
├── cpp/             # C / C++ style, hooks, security
├── figma/           # Figma Code Connect & design system rules
├── golang/          # Go idiomatic rules
├── python/          # Python PEP8/ruff/bandit rules
├── react/           # React components, hooks, patterns, testing
├── react-native/    # React Native / Expo readiness & security
├── rust/            # Rust ownership, clippy, cargo rules
├── typescript/      # TypeScript/JavaScript style, hooks, security
├── vue/             # Vue 3 rules
└── web/             # Web quality & security
```

- **common/** contains language-agnostic engineering contracts (`AGENTS.md` invariants, coding style, token economy, Gravitas invariants, testing, git workflow, security).
- **Language directories** extend `../common/` with stack-specific conventions and take precedence on conflicts.

## Installation

Installers (`installer/setup.ps1` and `installer/setup.sh`) automatically copy `rules/` into `~/.gemini/config/rules/`.

For manual deployment, copy entire directories so relative `../common/` references remain intact:

```bash
mkdir -p ~/.gemini/config/rules
cp -r rules/common ~/.gemini/config/rules/
cp -r rules/python rules/typescript ~/.gemini/config/rules/
```
