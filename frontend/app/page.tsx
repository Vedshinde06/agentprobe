"use client";

import { useEffect, useRef, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Verdict = "pass" | "fail" | "partial" | "judge_error";
type RunStatus = "pending" | "running" | "done" | "failed";

interface TestResultSummary {
  test_id: string;
  category: string;
  verdict: Verdict | null;
  latency_ms: number | null;
}

interface RunSummary {
  category_scores: Record<string, number>;
  total_tests: number;
  passed: number;
  failed: number;
}

interface Run {
  run_id: string;
  status: RunStatus;
  endpoint_url: string;
  corpus_id: string;
  created_at: string;
  summary: RunSummary | null;
  tests: TestResultSummary[];
}

const VERDICT_COLORS: Record<string, string> = {
  pass: "bg-green-100 text-green-800",
  fail: "bg-red-100 text-red-800",
  partial: "bg-yellow-100 text-yellow-800",
  judge_error: "bg-gray-100 text-gray-800",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  done: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function Home() {
  const [endpointUrl, setEndpointUrl] = useState("https://httpbin.org/post");
  const [runId, setRunId] = useState<string | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setIsPolling(false);
  };

  const fetchRun = async (id: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/runs/${id}`);
      if (!res.ok) return;
      const data: Run = await res.json();
      setRun(data);
      if (data.status === "done" || data.status === "failed") {
        stopPolling();
      }
    } catch {
      // network hiccup — keep polling
    }
  };

  const startRun = async () => {
    setError(null);
    setRun(null);
    setRunId(null);
    stopPolling();
    try {
      const res = await fetch(`${BACKEND_URL}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint_url: endpointUrl, corpus_id: "demo" }),
      });
      if (!res.ok) {
        setError(`Failed to start run: ${res.status}`);
        return;
      }
      const data = await res.json();
      const id: string = data.run_id;
      setRunId(id);
      setIsPolling(true);
      await fetchRun(id);
      pollRef.current = setInterval(() => fetchRun(id), 1000);
    } catch (e) {
      setError(`Error: ${e}`);
    }
  };

  // cleanup on unmount
  useEffect(() => () => stopPolling(), []);

  const handleTestClick = async (testId: string) => {
    if (!runId) return;
    const res = await fetch(`${BACKEND_URL}/runs/${runId}/tests/${testId}`);
    const data = await res.json();
    console.log("Test detail:", data);
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-8 font-mono">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold tracking-tight mb-1">AgentProbe</h1>
        <p className="text-gray-400 mb-8 text-sm">
          Stress-tests your RAG agent — surfaces where it fails.
        </p>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={endpointUrl}
            onChange={(e) => setEndpointUrl(e.target.value)}
            placeholder="RAG endpoint URL"
            className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={startRun}
            disabled={isPolling}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 px-4 py-2 rounded text-sm font-semibold transition-colors"
          >
            {isPolling ? "Running…" : "Run Evaluation"}
          </button>
        </div>

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        {run && (
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">Status:</span>
              <span
                className={`text-xs px-2 py-1 rounded font-semibold ${STATUS_COLORS[run.status] ?? ""}`}
              >
                {run.status}
              </span>
              {run.summary && (
                <span className="text-xs text-gray-500">
                  {run.summary.passed}/{run.summary.total_tests} passed
                </span>
              )}
            </div>

            {run.summary &&
              Object.keys(run.summary.category_scores).length > 0 && (
                <div>
                  <h2 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                    Category Scores
                  </h2>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {Object.entries(run.summary.category_scores).map(
                      ([cat, score]) => (
                        <div
                          key={cat}
                          className="bg-gray-800 rounded p-3 flex justify-between items-center"
                        >
                          <span className="text-xs text-gray-400 capitalize">
                            {cat}
                          </span>
                          <span className="text-sm font-bold text-white">
                            {score.toFixed(2)}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

            {run.tests.length > 0 && (
              <div>
                <h2 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                  Test Results
                </h2>
                <div className="space-y-1">
                  {run.tests.map((t) => (
                    <button
                      key={t.test_id}
                      onClick={() => handleTestClick(t.test_id)}
                      className="w-full flex items-center justify-between bg-gray-800 hover:bg-gray-700 rounded px-3 py-2 text-left transition-colors"
                    >
                      <span className="text-xs text-gray-400">
                        {t.category} — {t.test_id}
                      </span>
                      <div className="flex items-center gap-2">
                        {t.latency_ms != null && (
                          <span className="text-xs text-gray-500">
                            {t.latency_ms}ms
                          </span>
                        )}
                        {t.verdict && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded font-semibold ${VERDICT_COLORS[t.verdict] ?? ""}`}
                          >
                            {t.verdict}
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
