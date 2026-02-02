"use client";
import { useState } from "react";
import { apiPost } from "../lib/api";

export default function Page() {
  const [target, setTarget] = useState("/workspace");
  const [jobId, setJobId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function createJob() {
    setErr(null);
    try {
      const res = await apiPost("/jobs", {
        target_path: target,
        ruleset: "rulesets/owasp-llm-top10.yml",
        ai_review: true,
        policy_path: "policies/default.yml"
      });
      setJobId(res.job_id);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  return (
    <main className="space-y-6">
      <section className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
        <h2 className="text-lg font-semibold">Create a scan job</h2>
        <p className="text-sm text-zinc-400 mt-1">
          Scans a path mounted into the API container (default: <code>/workspace</code>).
        </p>

        <div className="mt-4 flex flex-col gap-2">
          <label className="text-sm text-zinc-300">Target path</label>
          <input
            className="px-3 py-2 rounded-xl bg-zinc-950 border border-zinc-800 text-zinc-100"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />
        </div>

        <div className="mt-4 flex gap-3 items-center">
          <button
            onClick={createJob}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium"
          >
            Run scan
          </button>
          {jobId && <a className="text-sm" href={`/jobs/${jobId}`}>View job →</a>}
        </div>

        {err && <p className="text-sm text-red-300 mt-3">{err}</p>}
      </section>

      <section className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
        <h2 className="text-lg font-semibold">What’s included</h2>
        <ul className="mt-2 text-sm text-zinc-300 list-disc ml-5 space-y-1">
          <li>Rules-based scan (YAML rulesets)</li>
          <li>Ollama judges validate findings (self-consistency)</li>
          <li>Policy-as-code decides allow/block/manual_review</li>
          <li>SARIF export per job</li>
          <li>Secure snippets library</li>
        </ul>
      </section>
    </main>
  );
}
