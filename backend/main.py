from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import db
from backend.runner import run_evaluation
from backend.schemas import (
    CreateRunRequest,
    CreateRunResponse,
    RunResponse,
    RunSummary,
    TestResult,
    TestResultSummary,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(title="AgentProbe", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://agentprobe-xi.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/runs", response_model=CreateRunResponse)
async def create_run(body: CreateRunRequest, background_tasks: BackgroundTasks):
    run_id = await db.create_run(str(body.endpoint_url), body.corpus_id)
    background_tasks.add_task(run_evaluation, run_id, str(body.endpoint_url), body.corpus_id)
    return CreateRunResponse(run_id=run_id, status="pending")


@app.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    row = await db.get_run(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    tests = await db.list_test_results(run_id)
    summary = RunSummary.model_validate_json(row["summary_json"]) if row["summary_json"] else None
    return RunResponse(
        run_id=row["id"],
        status=row["status"],
        endpoint_url=row["endpoint_url"],
        corpus_id=row["corpus_id"],
        created_at=row["created_at"],
        summary=summary,
        tests=[
            TestResultSummary(
                test_id=t.test_id,
                category=t.category,
                verdict=t.judge.verdict if t.judge else None,
                latency_ms=t.latency_ms,
            )
            for t in tests
        ],
    )


@app.get("/runs/{run_id}/tests/{test_id}", response_model=TestResult)
async def get_test_result(run_id: str, test_id: str):
    result = await db.get_test_result(run_id, test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result
