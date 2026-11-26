"""On-demand zero-click automation, workspace audit, and checkpoint stubs."""

from server import (
    audit_workspace_tokens,
    auto_setup_environment,
    cache_prefix_audit,
    clear_chat_history,
    create_checkpoint,
    restore_checkpoint,
    run_health_doctor,
)

__all__ = [
    "audit_workspace_tokens",
    "auto_setup_environment",
    "cache_prefix_audit",
    "clear_chat_history",
    "create_checkpoint",
    "restore_checkpoint",
    "run_health_doctor",
]
