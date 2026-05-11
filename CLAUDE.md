# CLAUDE.md — AgentProbe

> Read this first. Every session. Don't ask the user to repeat the context below.

## What this project is

AgentProbe is a 4-day prototype that stress-tests RAG agents and surfaces
where they fail. Built for the Activate AI Fellowship application, deadline
**May 15, 2026**.

User pastes a RAG endpoint URL + uploads corpus → AgentProbe runs ~30
adversarial tests across 5 categories → live dashboard shows pass/fail
with clickable failure inspection (question, retrieved chunks, judge
reasoning, side-by-side).

The submission is judged by:
- A deployed working URL (not localhost)
- A 90-second video demo
- The GitHub repo + README

## The 5 eval categories (locked — do not add a 6th)

1. **Grounding** — claims in response not supported by retrieved chunks
2. **Refusal** — adversarial out-of-corpus questions that *should* return "I don't know"
3. **Code-switch robustness** — same question in English / Hinglish (Latin) / Devanagari Hindi → answer consistency. **This is the wedge. Indian-language code-switching is the project's differentiator.**
4. **Multi-hop** — questions requiring 2+ retrieved chunks
5. **Latency** — P50/P95 response time, token usage

## Tech stack (locked — do not suggest alternatives)

- **Backend:** FastAPI, plain async Python with `asyncio.gather`
- **Judge LLM:** Google Gemini 2.5 Flash via `google-genai` SDK (user has keys from his Padcare internship)
- **Storage:** SQLite, single file. No Postgres, no Redis.
- **Frontend:** Next.js + Tailwind + shadcn/ui (fallback: Streamlit if Next gets stuck on Day 1)
- **Deploy:** Backend on Railway, frontend on Vercel. No Docker until Day 4 if there's time.
- **Embeddings (for code-switch consistency scoring):** FastEmbed (small, ONNX-based, no GPU needed)

## What this project is NOT — refuse to build any of these

- ❌ **LangGraph orchestration** — plain `asyncio.gather` is correct here. LangGraph adds zero value for parallel test execution and 4 hours of debugging cost. If the user asks for it, push back.
- ❌ Multiple LLM providers — Gemini Flash only
- ❌ User auth — single-user demo
- ❌ Custom retrieval / embeddings for the agent itself (we evaluate, we don't retrieve)
- ❌ Docker until Day 4
- ❌ Streaming responses — `await` and show
- ❌ A "polished landing page" — the dashboard IS the landing page
- ❌ Microservices, queues, Celery, anything distributed

If the user asks for any of these, remind them of the deadline and the
"locked list" before writing code. Founder energy = ruthless scope.

## Repo structure (do not deviate)

```
agentprobe/
├── backend/
│   ├── main.py           # FastAPI app — 3 routes only
│   ├── runner.py         # Orchestrates test execution
│   ├── judge.py          # Gemini-based LLM judge
│   ├── tests/
│   │   ├── grounding.py
│   │   ├── refusal.py
│   │   ├── codeswitch.py
│   │   ├── multihop.py
│   │   └── latency.py
│   ├── db.py             # SQLite wrapper, ~50 lines
│   ├── schemas.py        # Pydantic models
│   └── test_corpus/      # Hardcoded test questions per category
├── frontend/             # Next.js app
├── corpus/               # Demo PDFs (RBI circulars, DPDP Act, SPPU syllabus)
└── README.md
```

## FastAPI routes (exactly 3 in v1)

- `POST /runs` — body: `{endpoint_url, corpus_id}` → creates run, returns `run_id`, kicks off async execution
- `GET /runs/{id}` — returns status (pending/running/done) + summary scores per category
- `GET /runs/{id}/tests/{test_id}` — returns full failure detail (question, response, chunks, judge reasoning)

No other routes unless user explicitly asks. No `/health`, no `/users`,
no `/auth`. Keep `main.py` under 80 lines.

## Judge prompt contract (do not change without asking)

The judge LLM always returns strict JSON:
```json
{
  "score": 0.0,
  "reasoning": "...",
  "unsupported_claims": ["..."],
  "verdict": "pass" | "fail" | "partial"
}
```

If parsing fails, retry once with stricter instructions, then mark the
test as `judge_error` (don't crash the run).

## Code-switch test design (your wedge — get this right)

For every code-switch test, generate 3 variants:
- `en`: English
- `hi_latin`: Hinglish in Latin script — natural, code-mixed, the way an Indian student actually types
- `hi_deva`: Devanagari script Hindi

**The Hinglish must sound authentic.** The user is fluent in
Hindi/Hinglish (Nagpur-based, Marathi/Hindi speaker). When generating
test cases, write naturalistic vernacular like:
- "OS ke end-sem ka marking scheme kya hai?"
- "Bhai is repo rate me kya difference aya hai last month se?"

NOT awkward LLM Hinglish like "Mujhe is documente ke baareme jaankaari chahiye."

**Default behavior:** when adding new code-switch tests, draft them in
English, then ask the user to provide the Hinglish + Devanagari versions
himself. Do not generate Hinglish without his review.

Score consistency by:
1. Get response for each variant
2. Embed all 3 responses with FastEmbed
3. Pairwise cosine similarity, min of 3 = consistency score
4. Judge LLM second-checks semantic equivalence

## Day-by-day milestones (the calendar matters more than features)

- **Day 1 (May 11):** Deployed URL exists. Fake test result renders end-to-end. **The pipeline works.** Ugly is fine.
- **Day 2 (May 12):** All 5 categories run real tests against the user's own SPPU Exam Assistant. Real numbers, real failures captured.
- **Day 3 (May 13):** Failure browser polished. Side-by-side view works. Run on 2 external systems if possible.
- **Day 4 (May 14):** Video recorded, README finalized, application submitted by evening (NOT May 15 midnight).

If we are behind on Day 2 evening, cut multi-hop test category first
(easiest to drop), then latency last (it's cheap to add).

## Testing the system under test (SUT)

The "official" demo SUT is the user's own SPPU Exam Assistant
(https://github.com/Vedshinde06/... — FastAPI + LangChain + FAISS). Use
it for all internal validation. He knows its weaknesses, which means we
get impressive failure screenshots cheaply.

For the video and benchmarks, we want to also run AgentProbe against
1-2 external systems. If no public RAG endpoint is findable by Day 3
morning, add a "Bring Your Own LLM" mode: user pastes Gemini key,
AgentProbe spins up a vanilla RAG against the bundled corpus, runs
tests against it. ~30 min of work.

## What "done" looks like for the application

1. Live URL at agentprobe.vercel.app (or similar) — paste endpoint, get dashboard
2. Public GitHub repo with the "What's broken" section in README intact
3. 90s video on Loom or YouTube unlisted
4. Application essays referencing real benchmark numbers from runs

## User context

- **Name:** Vedant Shinde, pre-final year AI/DS undergrad in Pune
- **Stack he ships in:** Python, FastAPI, Docker, GCP, LangChain, LangGraph, FAISS
- **Current internship:** Padcare Labs (production RAG with Gemini)
- **Time budget:** ~6 hours/day for 4 days = 24 hours total
- **Hindi/Hinglish:** Fluent — can write authentic test cases
- **Has not used:** MCP protocol, raw Claude Code agentic workflows
- **Risk profile:** Tends toward over-engineering and ambitious scope.
  Push back when he tries to add features. Remind him of the deadline.

## Working style preferences

- Be direct. Don't soften feedback.
- Show file diffs, don't paraphrase changes.
- When suggesting commands, give the exact command, not a description.
- If a tool/library could fail (rate limits, deploy quirks), say so upfront.
- Cite real Gemini/FastAPI/FastEmbed docs when behavior is non-obvious — don't guess from training data, especially for Gemini 2.5 Flash API surface, which changes frequently.

## Commit hygiene

Public repo, visible history. Commit early and often. Good commit
messages tell the May 11 → May 14 story:
- ✅ "feat: code-switch test category, en/hi_latin/hi_deva variants"
- ❌ "wip", "update", "fixes"

Push at least every 2 hours of work. Showing a steady commit cadence in
the repo is part of the submission signal.

## When stuck

Default fallback hierarchy if something blocks the timeline:
1. Cut the feature
2. Hardcode the value
3. Mock the dependency
4. Ship it broken with a note in "What's broken" section

Never: spend more than 30 minutes debugging a single deploy / library issue without escalating to the user with "this is taking too long, here are 3 alternatives."
