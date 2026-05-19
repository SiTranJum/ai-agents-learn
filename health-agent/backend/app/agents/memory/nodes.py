"""Memory subgraph nodes."""

from __future__ import annotations

import logging
from typing import Any, cast

from app.agents._logging import log_llm_call, log_node
from app.agents.base import get_chat_model
from app.agents.memory.state import MemoryExtractionState
from app.agents.memory.tools import list_existing_memories_tool, save_memory_tool
from app.agents.prompts.consolidate import build_consolidate_messages
from app.agents.prompts.memory_extract import build_memory_extract_messages
from app.agents.prompts.memory_score import build_memory_score_messages
from app.schemas.memory import (
    ConsolidatedMemorySummary,
    ExtractedMemory,
    MemoryCreate,
    MemoryExtractionResult,
    MemoryQualityScore,
    MemoryScoreResult,
    MemoryStatus,
    MemorySummaryCreate,
)

logger = logging.getLogger(__name__)


def _get_service(state: MemoryExtractionState):
    return cast(Any, state).get("memory_service")


def _get_embedding_client(state: MemoryExtractionState):
    return cast(Any, state).get("embedding_client")


@log_node
async def extract(state: MemoryExtractionState) -> dict[str, Any]:
    """Use LLM structured output to extract durable memories from context."""
    try:
        chat_model = cast(Any, get_chat_model(temperature=0.1, timeout=30))
        model = chat_model.with_structured_output(MemoryExtractionResult)
        log_llm_call("extract", "qwen-plus", trigger_type=state.get("trigger_type", "unknown"))
        result = await model.ainvoke(
            build_memory_extract_messages(
                state.get("trigger_type", "unknown"),
                state.get("context_data", {}),
            )
        )
        return {"extracted": result.memories}
    except Exception as exc:  # pragma: no cover - defensive no-op path
        logger.warning("memory extraction failed: %s", exc)
        return {"extracted": [], "error": "memory_extraction_failed"}


@log_node
async def score(state: MemoryExtractionState) -> dict[str, Any]:
    """Use LLM structured output to score extracted memories."""
    memories = [memory for memory in state.get("extracted", []) if isinstance(memory, ExtractedMemory)]
    if not memories:
        return {"scored": []}
    service = _get_service(state)
    existing = state.get("existing_memories")
    if existing is None and service is not None:
        existing = await list_existing_memories_tool(service, limit=20)
    try:
        chat_model = cast(Any, get_chat_model(temperature=0.0, timeout=30))
        model = chat_model.with_structured_output(MemoryScoreResult)
        log_llm_call("score", "qwen-plus", memories_count=len(memories))
        result = await model.ainvoke(build_memory_score_messages(memories, existing or []))
        return {"scored": result.scored_memories}
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("memory scoring failed: %s", exc)
        fallback = [
            MemoryQualityScore(
                memory_type=memory.memory_type,
                content=memory.content,
                metadata=memory.metadata,
                source=memory.source,
                relevance=70,
                accuracy=70,
                actionability=70,
                uniqueness=70,
                overall_score=70,
                reason="fallback score after scorer failure",
            )
            for memory in memories
        ]
        return {"scored": fallback, "error": "memory_scoring_failed"}


@log_node
async def filter_memories(state: MemoryExtractionState) -> dict[str, Any]:
    """Deterministically filter scored memories into active or pending entries."""
    approved: list[MemoryCreate] = []
    for item in state.get("scored", []) or []:
        if item.overall_score < 60:
            continue
        status = MemoryStatus.active if item.overall_score >= 80 else MemoryStatus.pending
        approved.append(
            MemoryCreate(
                memory_type=item.memory_type,
                content=item.content,
                embedding=[0.0],
                metadata=item.metadata,
                quality_score=item.overall_score,
                status=status,
                source=item.source,
                trigger_type=state.get("trigger_type"),
            )
        )
    return {"approved": approved}


@log_node
async def embed_and_store(state: MemoryExtractionState) -> dict[str, Any]:
    """Generate embeddings for approved memories and persist them via MemoryService."""
    service = _get_service(state)
    embedding_client = _get_embedding_client(state)
    if service is None or embedding_client is None:
        return {"stored": [], "error": "memory_dependencies_missing"}
    stored = []
    for memory in state.get("approved", []) or []:
        embedding = await embedding_client.embed(memory.content)
        stored.append(await save_memory_tool(service, memory.model_copy(update={"embedding": embedding})))
    return {"stored": stored}


@log_node
async def consolidate(state: MemoryExtractionState) -> dict[str, Any]:
    """Summarize similar memories and archive their source entries."""
    memories = state.get("consolidate_memories", []) or []
    service = _get_service(state)
    if not memories or service is None:
        return {}
    chat_model = cast(Any, get_chat_model(temperature=0.1, timeout=60))
    model = chat_model.with_structured_output(ConsolidatedMemorySummary)
    log_llm_call("consolidate", "qwen-plus", memories_count=len(memories))
    result = await model.ainvoke(build_consolidate_messages(memories))
    period_start = min(memory.created_at.date() for memory in memories)
    period_end = max(memory.created_at.date() for memory in memories)
    summary = await service.create_summary(
        MemorySummaryCreate(
            period_start=period_start,
            period_end=period_end,
            summary_content=result.summary_content,
            key_facts=result.key_facts,
            source_memory_ids=[memory.id for memory in memories],
            quality_score=result.quality_score,
        )
    )
    await service.archive_memories([memory.id for memory in memories])
    return {"summary": summary}


__all__ = ["consolidate", "embed_and_store", "extract", "filter_memories", "score"]



