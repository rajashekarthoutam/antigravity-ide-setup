# MCP Tools-as-Files API (Code-Mode 90%+ Token Reduction)

Instead of injecting 26+ full JSON tool schemas into every prompt, agents discover and import only the lightweight Python stubs they need inside `execute_code_sandbox()`.

Modules (`from tools_api.<module> import ...`):
- `infinite_context.py`: `compact_conversation_loop`, `virtualize_output`, `search_virtual_context`, `fetch_virtual_slice`, `cli_compress`, `redact_secrets`
- `navigation.py`: `pagerank_repo_map`, `get_file_outline`, `get_symbol`, `code_reference_probe`, `code_graph_impact_probe`, `safe_read_file`, `diff_re_read`, `repo_shape_probe`, `structural_diff`, `validate_syntax`, `github_agentic_probe`
- `sandbox_filter.py`: `execute_code_sandbox`, `filter_and_loop_data`, `system1_triage`, `speculative_sandbox`, `count_tokens`, `to_toon`, `cache_lookup_or_store`
- `memory_graph.py`: `add_memory`, `search_memories`, `record_side_effect`, `query_side_effects`, `record_failure_reflexion`, `query_failure_reflexions`
- `security_eval.py`: `evaluate_skill`, `verify_agent_skill`, `audit_agent_safety`, `model_armor_sanitize`, `validate_a2a_handoff`, `get_agent_card`, `list_agent_cards`, `search_skills`, `synthesize_skill`
- `automation.py`: `auto_setup_environment`, `clear_chat_history`, `run_health_doctor`, `audit_workspace_tokens`, `cache_prefix_audit`, `create_checkpoint`, `restore_checkpoint`
