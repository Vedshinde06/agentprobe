import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from backend.schemas import JudgeResult, RunStatus, RunSummary, TestResult

DB_PATH = Path(__file__).parent / "agentprobe.db"
# TODO Day 3: Railway filesystem resets on redeploy — DB_PATH is ephemeral.
# Switch to Railway volume mount: set DB_PATH = Path(os.environ["RAILWAY_VOLUME_MOUNT_PATH"]) / "agentprobe.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                endpoint_url TEXT NOT NULL,
                corpus_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                summary_json TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                category TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT,
                retrieved_chunks_json TEXT,
                judge_json TEXT,
                latency_ms INTEGER,
                error TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)
        await db.commit()


async def create_run(endpoint_url: str, corpus_id: str) -> str:
    run_id = uuid.uuid4().hex
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO runs (id, status, endpoint_url, corpus_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, RunStatus.pending, endpoint_url, corpus_id, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
    return run_id


async def update_run_status(run_id: str, status: RunStatus) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))
        await db.commit()


async def save_summary(run_id: str, summary: RunSummary) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE runs SET summary_json = ?, status = ? WHERE id = ?",
            (summary.model_dump_json(), summary.status, run_id),
        )
        await db.commit()


async def get_run(run_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def save_test_result(run_id: str, result: TestResult) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO test_results
               (id, run_id, category, question, response, retrieved_chunks_json,
                judge_json, latency_ms, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.test_id, run_id, result.category, result.question,
                result.response, json.dumps(result.retrieved_chunks),
                result.judge.model_dump_json() if result.judge else None,
                result.latency_ms, result.error,
            ),
        )
        await db.commit()


async def get_test_result(run_id: str, test_id: str) -> TestResult | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM test_results WHERE run_id = ? AND id = ?", (run_id, test_id)
        ) as cur:
            row = await cur.fetchone()
            return _row_to_test_result(row) if row else None


async def list_test_results(run_id: str) -> list[TestResult]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM test_results WHERE run_id = ?", (run_id,)) as cur:
            rows = await cur.fetchall()
            return [_row_to_test_result(r) for r in rows]


def _row_to_test_result(row: aiosqlite.Row) -> TestResult:
    return TestResult(
        test_id=row["id"],
        category=row["category"],
        question=row["question"],
        response=row["response"],
        retrieved_chunks=json.loads(row["retrieved_chunks_json"] or "[]"),
        judge=JudgeResult.model_validate_json(row["judge_json"]) if row["judge_json"] else None,
        latency_ms=row["latency_ms"],
        error=row["error"],
    )
