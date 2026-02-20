"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, API_BASE } from "../../../lib/api";

export default function JobDetail() {
  const params = useParams<{ id: string }>();
  const rawId = params?.id;
  const jobId = Array.isArray(rawId) ? rawId[0] : rawId;
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    if (!jobId) return;
    setErr(null);
    try {
      const r = await apiGet(`/jobs/${jobId}/results`);
      setData(r);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  useEffect(() => {
    if (!jobId) return;
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [jobId]);

  const sarifUrl = `${API_BASE}/jobs/${jobId}/sarif`;

  return (
    <main className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Job</h2>
        <div className="flex gap-2">
          {jobId && (
            <a href={sarifUrl} className="px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-sm">
              Download SARIF
            </a>
          )}
          <button onClick={load} className="px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-sm">
            Refresh
          </button>
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
        <div className="font-mono text-sm">{jobId || "loading..."}</div>
        {data?.job && (
          <div className="text-xs text-zinc-400 mt-2 space-y-1">
            <div>Status: {data.job.status}</div>
            <div>Decision: <span className="text-zinc-200">{data.job.decision}</span></div>
            {data.job.decision_reason && <div>Reason: {data.job.decision_reason}</div>}
          </div>
        )}
      </div>

      {err && <p className="text-sm text-red-300">{err}</p>}

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Findings</h3>
        <div className="grid gap-3">
          {(data?.findings || []).map((f: any, idx: number) => (
            <div key={idx} className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
              <div className="flex justify-between">
                <div className="font-semibold">{f.rule_id} • {f.title}</div>
                <div className="text-xs text-zinc-300">{f.severity}</div>
              </div>
              <div className="text-xs text-zinc-400 mt-1">{f.file}:{f.line}</div>
              {f.message && <div className="text-sm text-zinc-200 mt-2">{f.message}</div>}
              {f.remediation && <div className="text-sm text-indigo-200 mt-2">Fix: {f.remediation}</div>}
              {f.match && <pre className="mt-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-x-auto">{f.match}</pre>}
            </div>
          ))}
          {(data?.findings || []).length === 0 && <p className="text-sm text-zinc-500">No findings yet (job may still be running).</p>}
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Model calls</h3>
        <div className="grid gap-3">
          {(data?.model_calls || []).map((c: any, idx: number) => (
            <div key={idx} className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
              <div className="text-sm">{c.provider}:{c.model} • {c.role}</div>
              {c.parsed && Object.keys(c.parsed).length > 0 && (
                <pre className="mt-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-x-auto">
                  {JSON.stringify(c.parsed, null, 2)}
                </pre>
              )}
              {c.response_excerpt && (
                <pre className="mt-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-x-auto text-zinc-200">
                  {c.response_excerpt}
                </pre>
              )}
            </div>
          ))}
          {(data?.model_calls || []).length === 0 && <p className="text-sm text-zinc-500">No model calls yet.</p>}
        </div>
      </section>
    </main>
  );
}
