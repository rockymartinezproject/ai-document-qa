"""
Evaluation endpoints for measuring RAG quality.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.models.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluationRunRequest,
    EvaluationMetrics,
)
from app.models.response import APIResponse
from app.services.evaluation import aggregate_metrics, evaluate_sample
from app.services.rag import answer_question

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])
logger = get_logger("evaluation_api")


def _metrics_from_dict(d: dict) -> EvaluationMetrics:
    return EvaluationMetrics(
        context_precision=d["context_precision"],
        answer_relevance=d["answer_relevance"],
        faithfulness=d["faithfulness"],
        overall=d["overall"],
    )


@router.post("/metrics", response_model=APIResponse[EvaluationResponse])
async def evaluate_metrics(
    request: Request,
    body: EvaluationRequest,
):
    """Evaluate pre-computed RAG outputs against a test set."""
    request_id = getattr(request.state, "request_id", None)

    results = []
    metric_rows = []
    for sample in body.samples:
        metrics = await evaluate_sample(
            query=sample.query,
            expected_answer=sample.expected_answer,
            contexts=sample.contexts,
            actual_answer=sample.actual_answer,
            retrieved_contexts=sample.retrieved_contexts,
        )
        metric_rows.append(metrics)
        results.append(
            EvaluationResult(
                query=sample.query,
                expected_answer=sample.expected_answer,
                actual_answer=sample.actual_answer,
                metrics=_metrics_from_dict(metrics),
            )
        )

    aggregate = aggregate_metrics(metric_rows)

    return APIResponse(
        success=True,
        data=EvaluationResponse(
            results=results,
            aggregate=_metrics_from_dict(aggregate),
        ),
        request_id=request_id,
    )


@router.post("/run", response_model=APIResponse[EvaluationResponse])
async def evaluate_run(
    request: Request,
    body: EvaluationRunRequest,
    session: AsyncSession = Depends(get_db),
):
    """Run RAG for each sample and then compute evaluation metrics."""
    request_id = getattr(request.state, "request_id", None)

    results = []
    metric_rows = []
    for sample in body.samples:
        try:
            rag_answer = await answer_question(
                query=sample.query,
                top_k=body.top_k,
                document_id=sample.document_id,
                session=session,
                rerank=body.rerank,
                provider=sample.provider,
                model=sample.model,
            )
        except Exception as exc:
            logger.warning("RAG failed for evaluation sample: %s", exc)
            rag_answer = type(
                "RAGAnswer",
                (),
                {"answer": "", "citations": [], "provider": "unknown"},
            )()

        retrieved_contexts = [c.text for c in rag_answer.citations]
        metrics = await evaluate_sample(
            query=sample.query,
            expected_answer=sample.expected_answer,
            contexts=[],
            actual_answer=rag_answer.answer,
            retrieved_contexts=retrieved_contexts,
        )
        metric_rows.append(metrics)
        results.append(
            EvaluationResult(
                query=sample.query,
                expected_answer=sample.expected_answer,
                actual_answer=rag_answer.answer,
                metrics=_metrics_from_dict(metrics),
            )
        )

    aggregate = aggregate_metrics(metric_rows)

    return APIResponse(
        success=True,
        data=EvaluationResponse(
            results=results,
            aggregate=_metrics_from_dict(aggregate),
        ),
        request_id=request_id,
    )
