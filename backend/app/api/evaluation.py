"""
Evaluation endpoints for measuring RAG quality.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import EvaluationRun
from app.models.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluationRunDetail,
    EvaluationRunOut,
    EvaluationRunRequest,
    EvaluationMetrics,
    GenerateDatasetRequest,
    GeneratedDatasetResponse,
)
from app.models.response import APIResponse
from app.services.evaluation import (
    aggregate_metrics,
    evaluate_sample,
    generate_dataset,
    has_regression,
)
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


@router.post("/generate", response_model=APIResponse[GeneratedDatasetResponse])
async def generate_test_dataset(
    request: Request,
    body: GenerateDatasetRequest,
    session: AsyncSession = Depends(get_db),
):
    """Generate synthetic Q&A pairs from a document's chunks."""
    request_id = getattr(request.state, "request_id", None)

    samples = await generate_dataset(
        session=session,
        document_id=body.document_id,
        sample_count=body.sample_count,
        provider_name=body.provider,
        model=body.model,
    )

    return APIResponse(
        success=True,
        data=GeneratedDatasetResponse(
            document_id=body.document_id,
            samples=samples,
        ),
        request_id=request_id,
    )


@router.post("/runs", response_model=APIResponse[EvaluationRunOut])
async def create_evaluation_run(
    request: Request,
    body: EvaluationRunRequest,
    session: AsyncSession = Depends(get_db),
):
    """Run RAG for each sample, compute metrics, and persist the results."""
    request_id = getattr(request.state, "request_id", None)

    run = EvaluationRun(
        name=body.name,
        status="running",
        sample_count=len(body.samples),
        samples=[s.model_dump() for s in body.samples],
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

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
            {
                "query": sample.query,
                "expected_answer": sample.expected_answer,
                "actual_answer": rag_answer.answer,
                "metrics": metrics,
            }
        )

    aggregate = aggregate_metrics(metric_rows)

    # Compare to the most recent previous completed run for regression detection
    previous = await session.execute(
        select(EvaluationRun)
        .where(EvaluationRun.status == "completed")
        .order_by(EvaluationRun.created_at.desc())
        .offset(1)
        .limit(1)
    )
    previous_run = previous.scalar_one_or_none()
    previous_overall = None
    if previous_run and previous_run.aggregate:
        previous_overall = previous_run.aggregate.get("overall")

    run.status = "completed"
    run.results = results
    run.aggregate = aggregate
    run.regression = int(has_regression(aggregate["overall"], previous_overall))
    await session.commit()
    await session.refresh(run)

    return APIResponse(
        success=True,
        data=EvaluationRunOut.model_validate(run),
        request_id=request_id,
    )


@router.get("/runs", response_model=APIResponse[list[EvaluationRunOut]])
async def list_evaluation_runs(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """List persisted evaluation runs with aggregate scores."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(
        select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
    )
    rows = result.scalars().all()

    return APIResponse(
        success=True,
        data=[EvaluationRunOut.model_validate(r) for r in rows],
        request_id=request_id,
    )


@router.get("/runs/{run_id}", response_model=APIResponse[EvaluationRunDetail])
async def get_evaluation_run(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get full details for a single evaluation run."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    return APIResponse(
        success=True,
        data=EvaluationRunDetail.model_validate(run),
        request_id=request_id,
    )


@router.delete("/runs/{run_id}", response_model=APIResponse[dict])
async def delete_evaluation_run(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Delete an evaluation run."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    await session.delete(run)
    await session.commit()

    return APIResponse(
        success=True,
        data={"deleted": True},
        request_id=request_id,
    )
