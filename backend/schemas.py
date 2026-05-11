from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class TestCategory(str, Enum):
    grounding = "grounding"
    refusal = "refusal"
    codeswitch = "codeswitch"
    multihop = "multihop"
    latency = "latency"


class Verdict(str, Enum):
    pass_ = "pass"
    fail = "fail"
    partial = "partial"
    judge_error = "judge_error"


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class CreateRunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    endpoint_url: AnyHttpUrl
    corpus_id: str


class JudgeResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    unsupported_claims: list[str]
    verdict: Verdict


class TestResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    test_id: str
    category: TestCategory
    question: str
    response: Optional[str] = None
    retrieved_chunks: list[str] = Field(default_factory=list)
    judge: Optional[JudgeResult] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class RunSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    run_id: str
    status: RunStatus
    endpoint_url: str
    created_at: datetime
    category_scores: dict[TestCategory, float] = Field(default_factory=dict)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0


class CreateRunResponse(BaseModel):
    run_id: str
    status: RunStatus


class TestResultSummary(BaseModel):
    test_id: str
    category: TestCategory
    verdict: Optional[Verdict] = None
    latency_ms: Optional[int] = None


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus
    endpoint_url: str
    corpus_id: str
    created_at: datetime
    summary: Optional[RunSummary] = None
    tests: list[TestResultSummary] = Field(default_factory=list)
