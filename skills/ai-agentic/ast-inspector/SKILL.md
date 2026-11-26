---
name: ast-inspector
description: Explores and inspects codebase structure using Tree-sitter AST queries via ast-grep to extract symbol signatures, class outlines, and interfaces without reading full source files.
---

# AST Inspector Skill

Use this skill to navigate, inspect, and extract code structure across any codebase with near-zero token consumption using `ast-grep` (which is pre-installed).

## When to Use
- You need to understand a class, module, or function signatures without loading hundreds of lines of code.
- You need to find where a method, interface, or struct is defined.
- You need to map out an entire directory or package architecture.

## Commands

### 1. View File / Directory Outline (Signatures Only)
Extracts top-level declarations (functions, classes, interfaces, types) and their type signatures:
```powershell
ast-grep outline --view signatures <file-or-dir>
```

### 2. View Compact Digest with Members
Extracts signatures along with a compact list of member functions and properties:
```powershell
ast-grep outline --view digest <file-or-dir>
```

### 3. Filter by Symbol Type
Only inspect specific constructs (e.g., classes, functions, interfaces):
```powershell
ast-grep outline --type class,function <file-or-dir>
```

### 4. Search by Regex Pattern
Find symbols matching a specific name pattern across the codebase:
```powershell
ast-grep outline --match "<pattern>" <dir>
```

### 5. Single-Line Compact JSON Output
For programmatic extraction with minimal output size:
```powershell
ast-grep outline --json=compact <file-or-dir>
```

## Token Optimization Rule
- After extracting signatures with `ast-grep outline`, note the exact line numbers.
- If you need to view the implementation details, call `view_file` specifying `StartLine` and `EndLine` for ONLY that function.
- Never dump whole files into chat or context.
