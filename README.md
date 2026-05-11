# AgentProbe

> Stress-tests RAG agents and surfaces where they actually fail.

🚀 **Live: https://agentprobe-xi.vercel.app**

[90s video](youtube/loom) · [Sample run](https://agentprobe-xi.vercel.app/runs/demo)

## Why

Every RAG agent works in demos. In production, they hallucinate, fail on
code-switched queries, and confidently answer questions they shouldn't.
There's no easy way for a small team to know *where* their agent breaks.

AgentProbe is a 4-day prototype that runs 30 adversarial tests against
any RAG endpoint and shows you the failures, with chunks and judge
reasoning side-by-side.

## What it tests

- **Grounding** — claims unsupported by retrieved chunks
- **Refusal** — should-be-IDK questions
- **Code-switch consistency** — EN / Hinglish / Devanagari for the same Q
- **Multi-hop** — needs 2+ chunks
- **Latency** — P50/P95

## What's broken

- Judge LLM (Gemini Flash) sometimes false-positives on grounding.
  Manual spot-check on a sample of 10 shows ~85% agreement.
- Multi-hop test set is small (5 questions). v2 should auto-generate from corpus.
- No auth. Don't paste endpoints with secrets.

## Built for the Activate AI Fellowship application, May 2026.