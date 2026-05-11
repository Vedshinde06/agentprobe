import time
from datetime import datetime

import httpx

from backend import db
from backend.schemas import (
    JudgeResult,
    RunStatus,
    RunSummary,
    TestCategory,
    TestResult,
    Verdict,
)


async def run_evaluation(run_id: str, endpoint_url: str, corpus_id: str) -> None:
    await db.update_run_status(run_id, RunStatus.running)

    question = "What is the repo rate?"
    test_id = "fake-test-1"

    response_text = None
    error = None
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(endpoint_url, json={"question": question})
            response_text = resp.text
    except Exception as exc:
        error = str(exc)
    latency_ms = int((time.monotonic() - start) * 1000)

    fake_judge = JudgeResult(
        score=0.42,
        verdict=Verdict.fail,
        reasoning="Hardcoded judge result for pipeline test — Hour 3 placeholder",
        unsupported_claims=["This is fake data, ignore"],
    )

    await db.save_test_result(
        run_id,
        TestResult(
            test_id=test_id,
            category=TestCategory.grounding,
            question=question,
            response=response_text,
            judge=fake_judge,
            latency_ms=latency_ms,
            error=error,
        ),
    )

    row = await db.get_run(run_id)
    summary = RunSummary(
        run_id=run_id,
        status=RunStatus.done,
        endpoint_url=endpoint_url,
        created_at=datetime.fromisoformat(row["created_at"]),
        category_scores={
            TestCategory.grounding: 0.42,
            TestCategory.refusal: 0.0,
            TestCategory.codeswitch: 0.0,
            TestCategory.multihop: 0.0,
            TestCategory.latency: 0.0,
        },
        total_tests=1,
        passed=0,
        failed=1,
    )
    await db.save_summary(run_id, summary)
