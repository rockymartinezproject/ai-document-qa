"""
Pydantic models for the evaluation API.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class EvaluationSample(BaseModel):
    """A single evaluation sample with expected and actual results."""

    query: str = Field(..., min_length=1, description="User question")
    expected_answer: str = Field(..., min_length=1, description="Reference answer")
    contexts: List[str] = Field(
        default_factory=list,
        description="Expected/gold context strings",
    )
    actual_answer: str = Field(
        default="",
        description="Generated answer to evaluate",
    )
    retrieved_contexts: List[str] = Field(
        default_factory=list,
        description="Context strings retrieved by the RAG pipeline",
    )


class EvaluationRunSample(BaseModel):
    """A sample used when the API runs RAG before scoring."""

    query: str = Field(..., min_length=1, description="User question")
    expected_answer: str = Field(..., min_length=1, description="Reference answer")
    document_id: Optional[str] = Field(
        default=None,
        description="Optional document filter for retrieval",
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider to use for generation",
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use for generation",
    )


class EvaluationMetrics(BaseModel):
    """Computed metrics for a single sample or an entire run."""

    context_precision: float = Field(..., ge=0.0, le=1.0)
    answer_relevance: float = Field(..., ge=0.0, le=1.0)
    faithfulness: float = Field(..., ge=0.0, le=1.0)
    overall: float = Field(..., ge=0.0, le=1.0)


class EvaluationResult(BaseModel):
    """Result for one sample, including inputs and scores."""

    query: str
    expected_answer: str
    actual_answer: str
    metrics: EvaluationMetrics


class EvaluationRequest(BaseModel):
    """Request body for evaluating pre-computed RAG outputs."""

    samples: List[EvaluationSample] = Field(..., min_length=1)


class EvaluationRunRequest(BaseModel):
    """Request body for running RAG and then evaluating."""

    samples: List[EvaluationRunSample] = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    search_type: str = Field(default="hybrid")
    rerank: bool = Field(default=True)


class EvaluationResponse(BaseModel):
    """Response containing per-sample results and aggregate scores."""

    results: List[EvaluationResult]
    aggregate: EvaluationMetrics
