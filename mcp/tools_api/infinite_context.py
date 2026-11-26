"""On-demand Infinite-Horizon Context Virtualization, FTS5 Search & Loop Compaction stubs."""

from infinite_context import (
    ContextVirtualizer,
    cli_compress,
    compact_conversation_loop,
    elide_output,
    fetch_virtual_slice,
    redact_secrets,
    run_compressed,
    search_virtual_context,
    virtualize_output,
)

__all__ = [
    "ContextVirtualizer",
    "cli_compress",
    "compact_conversation_loop",
    "elide_output",
    "fetch_virtual_slice",
    "redact_secrets",
    "run_compressed",
    "search_virtual_context",
    "virtualize_output",
]
