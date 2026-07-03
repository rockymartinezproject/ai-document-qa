"use client";

import { useEffect, useState } from "react";
import { api, DocumentOut, EvaluationRun, GeneratedSample, LLMProviderInfo } from "@/lib/api";
import { LoadingCard } from "@/components/Loading";
import { showToast } from "@/components/Toast";

function formatScore(n: number): string {
  return (n * 100).toFixed(1) + "%";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function EvaluatePage() {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [providers, setProviders] = useState<LLMProviderInfo[]>([]);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState<string>("mock");
  const [sampleCount, setSampleCount] = useState(3);
  const [generated, setGenerated] = useState<GeneratedSample[]>([]);
  const [runName, setRunName] = useState("Evaluation run");
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [running, setRunning] = useState(false);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<Record<string, Awaited<ReturnType<typeof api.evaluation.getRun>>["data"]>>({});

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [docsRes, providersRes, runsRes] = await Promise.all([
          api.documents.list(),
          api.providers.list(),
          api.evaluation.listRuns(),
        ]);
        if (cancelled) return;
        setDocuments(docsRes.data || []);
        const provs = providersRes.data || [];
        setProviders(provs);
        const firstAvailable = provs.find((p) => p.available);
        if (firstAvailable) setSelectedProvider(firstAvailable.name);
        setRuns(runsRes.data || []);
      } catch (e) {
        if (!cancelled) {
          console.error(e);
          showToast("Failed to load evaluation data", "error");
        }
      } finally {
        if (!cancelled) {
          setLoadingDocs(false);
          setLoadingRuns(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleGenerate = async () => {
    if (!selectedDoc) return;
    setGenerating(true);
    try {
      const res = await api.evaluation.generate(selectedDoc, sampleCount, selectedProvider);
      setGenerated(res.data?.samples || []);
      showToast(`Generated ${res.data?.samples.length || 0} samples`, "success");
    } catch (e) {
      console.error(e);
      showToast("Failed to generate dataset", "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleRun = async () => {
    if (generated.length === 0) return;
    setRunning(true);
    try {
      const res = await api.evaluation.createRun({
        name: runName,
        samples: generated.map((s) => ({
          query: s.query,
          expected_answer: s.expected_answer,
          document_id: selectedDoc,
          provider: selectedProvider,
        })),
        top_k: 5,
        rerank: false,
      });
      setRuns((prev) => [res.data!, ...prev]);
      showToast("Evaluation run completed", "success");
    } catch (e) {
      console.error(e);
      showToast("Failed to run evaluation", "error");
    } finally {
      setRunning(false);
    }
  };

  const toggleExpand = async (id: string) => {
    if (expandedRun === id) {
      setExpandedRun(null);
      return;
    }
    setExpandedRun(id);
    if (!runDetail[id]) {
      try {
        const res = await api.evaluation.getRun(id);
        setRunDetail((prev) => ({ ...prev, [id]: res.data }));
      } catch (e) {
        console.error(e);
        showToast("Failed to load run details", "error");
      }
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.evaluation.deleteRun(id);
      setRuns((prev) => prev.filter((r) => r.id !== id));
      setExpandedRun(null);
      showToast("Run deleted", "success");
    } catch (e) {
      console.error(e);
      showToast("Failed to delete run", "error");
    }
  };

  if (loadingDocs) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Evaluation Suite</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Evaluation Suite</h2>
      <p className="mt-2 text-zinc-600 dark:text-zinc-400">
        Generate test datasets, run batch evaluations, and detect regressions.
      </p>

      {/* Dataset generation */}
      <div className="mt-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">1. Generate Test Dataset</h3>
        <div className="mt-4 flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-zinc-500 dark:text-zinc-400">Document</label>
            <select
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              className="mt-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            >
              <option value="">Select a document</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-500 dark:text-zinc-400">Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="mt-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            >
              {providers.map((p) => (
                <option key={p.name} value={p.name} disabled={!p.available}>
                  {p.label} {!p.available ? "(no key)" : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-500 dark:text-zinc-400">Samples</label>
            <input
              type="number"
              min={1}
              max={20}
              value={sampleCount}
              onChange={(e) => setSampleCount(parseInt(e.target.value, 10) || 1)}
              className="mt-1 w-20 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={!selectedDoc || generating}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {generating ? "Generating..." : "Generate"}
          </button>
        </div>

        {generated.length > 0 && (
          <div className="mt-6">
            <h4 className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Generated Samples</h4>
            <div className="mt-2 max-h-64 overflow-y-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-zinc-50 dark:bg-zinc-800">
                  <tr>
                    <th className="px-3 py-2 font-medium text-zinc-600 dark:text-zinc-400">Question</th>
                    <th className="px-3 py-2 font-medium text-zinc-600 dark:text-zinc-400">Expected Answer</th>
                  </tr>
                </thead>
                <tbody>
                  {generated.map((s, i) => (
                    <tr key={i} className="border-t border-zinc-100 dark:border-zinc-800">
                      <td className="px-3 py-2 text-zinc-800 dark:text-zinc-200">{s.query}</td>
                      <td className="px-3 py-2 text-zinc-600 dark:text-zinc-400">{s.expected_answer}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Run evaluation */}
      {generated.length > 0 && (
        <div className="mt-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">2. Run Batch Evaluation</h3>
          <div className="mt-4 flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs font-medium text-zinc-500 dark:text-zinc-400">Run name</label>
              <input
                type="text"
                value={runName}
                onChange={(e) => setRunName(e.target.value)}
                className="mt-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
            </div>
            <button
              onClick={handleRun}
              disabled={running}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {running ? "Running..." : "Run Evaluation"}
            </button>
          </div>
        </div>
      )}

      {/* Runs list */}
      <div className="mt-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Evaluation Runs</h3>
        {loadingRuns ? (
          <LoadingCard />
        ) : runs.length === 0 ? (
          <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">No evaluation runs yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800">
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">Name</th>
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">Status</th>
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">Samples</th>
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">Overall</th>
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">Regression</th>
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">Created</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <>
                    <tr
                      key={run.id}
                      className="border-b border-zinc-100 last:border-0 dark:border-zinc-800/50 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                      onClick={() => toggleExpand(run.id)}
                    >
                      <td className="py-3 font-medium text-zinc-900 dark:text-zinc-100">{run.name}</td>
                      <td className="py-3 text-zinc-600 dark:text-zinc-400">{run.status}</td>
                      <td className="py-3 text-zinc-600 dark:text-zinc-400">{run.sample_count}</td>
                      <td className="py-3 text-zinc-600 dark:text-zinc-400">
                        {run.aggregate ? formatScore(run.aggregate.overall) : "—"}
                      </td>
                      <td className="py-3">
                        {run.regression ? (
                          <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                            Yes
                          </span>
                        ) : (
                          <span className="text-zinc-400 dark:text-zinc-600">No</span>
                        )}
                      </td>
                      <td className="py-3 text-zinc-500 dark:text-zinc-500">{formatDate(run.created_at)}</td>
                      <td className="py-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(run.id);
                          }}
                          className="text-xs text-red-600 hover:underline dark:text-red-400"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                    {expandedRun === run.id && runDetail[run.id] && (
                      <tr>
                        <td colSpan={7} className="bg-zinc-50 px-4 py-4 dark:bg-zinc-900">
                          <div className="space-y-3">
                            {runDetail[run.id]?.results?.map((r, i) => (
                              <div
                                key={i}
                                className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950"
                              >
                                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{r.query}</p>
                                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                                  Overall: {formatScore(r.metrics.overall)} · Precision:{" "}
                                  {formatScore(r.metrics.context_precision)} · Relevance:{" "}
                                  {formatScore(r.metrics.answer_relevance)} · Faithfulness:{" "}
                                  {formatScore(r.metrics.faithfulness)}
                                </p>
                                <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                                  <span className="font-medium">Expected:</span> {r.expected_answer}
                                </p>
                                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                                  <span className="font-medium">Actual:</span> {r.actual_answer || "—"}
                                </p>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
