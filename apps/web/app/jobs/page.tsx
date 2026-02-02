"use client";
import { useEffect, useState } from "react";
import { apiGet } from "../../lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      setJobs(await apiGet("/jobs"));
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);

  return (
    <main className="space-y-4">
      <h2 className="text-xl font-semibold">Jobs</h2>
      {err && <p className="text-sm text-red-300">{err}</p>}

      <div className="grid gap-3">
        {jobs.map((j) => (
          <a key={j.id} href={`/jobs/${j.id}`} className="block p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700">
            <div className="flex justify-between items-center">
              <div className="font-mono text-sm">{j.id}</div>
              <div className="text-xs text-zinc-300">{j.status}</div>
            </div>
            <div className="flex justify-between mt-1 text-xs text-zinc-500">
              <span>decision: {j.decision}</span>
              <span>{j.created_at}</span>
            </div>
          </a>
        ))}
        {jobs.length === 0 && <p className="text-sm text-zinc-500">No jobs yet.</p>}
      </div>
    </main>
  );
}
