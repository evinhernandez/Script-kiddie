"use client";
import { useEffect, useState } from "react";
import { apiGet } from "../../lib/api";

interface Stats {
  total_jobs: number;
  total_findings: number;
  total_model_calls: number;
  total_estimated_cost_usd: number;
  by_severity: Record<string, number>;
  by_decision: Record<string, number>;
  top_rules: { rule_id: string; count: number }[];
}

const SEV_COLORS: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-blue-500",
};

const DECISION_COLORS: Record<string, string> = {
  block: "bg-red-500",
  manual_review: "bg-yellow-500",
  allow: "bg-green-500",
};

function Bar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-28 text-zinc-400">{label}</span>
      <div className="flex-1 h-5 bg-zinc-800 rounded-lg overflow-hidden">
        <div className={`h-full ${color} rounded-lg`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-zinc-300">{value}</span>
    </div>
  );
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiGet("/stats")
      .then(setStats)
      .catch((e) => setErr(e.message || String(e)));
  }, []);

  if (err) return <p className="text-red-300">Error: {err}</p>;
  if (!stats) return <p className="text-zinc-400">Loading...</p>;

  const sevMax = Math.max(...Object.values(stats.by_severity), 1);
  const decMax = Math.max(...Object.values(stats.by_decision), 1);

  return (
    <main className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Jobs", value: stats.total_jobs },
          { label: "Total Findings", value: stats.total_findings },
          { label: "Model Calls", value: stats.total_model_calls },
          { label: "Est. Cost (USD)", value: `$${stats.total_estimated_cost_usd.toFixed(4)}` },
        ].map((card) => (
          <div key={card.label} className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 text-center">
            <p className="text-2xl font-bold text-zinc-100">{card.value}</p>
            <p className="text-xs text-zinc-400 mt-1">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Severity breakdown */}
      <section className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
        <h2 className="text-lg font-semibold mb-4">Findings by Severity</h2>
        <div className="space-y-2">
          {["critical", "high", "medium", "low"].map((sev) => (
            <Bar
              key={sev}
              label={sev}
              value={stats.by_severity[sev] || 0}
              max={sevMax}
              color={SEV_COLORS[sev] || "bg-zinc-500"}
            />
          ))}
        </div>
      </section>

      {/* Decision breakdown */}
      <section className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
        <h2 className="text-lg font-semibold mb-4">Jobs by Decision</h2>
        <div className="space-y-2">
          {["block", "manual_review", "allow"].map((dec) => (
            <Bar
              key={dec}
              label={dec.replace("_", " ")}
              value={stats.by_decision[dec] || 0}
              max={decMax}
              color={DECISION_COLORS[dec] || "bg-zinc-500"}
            />
          ))}
        </div>
      </section>

      {/* Top rules */}
      <section className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
        <h2 className="text-lg font-semibold mb-4">Top Rules</h2>
        {stats.top_rules.length === 0 ? (
          <p className="text-zinc-400 text-sm">No findings yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-zinc-400 border-b border-zinc-800">
                <th className="text-left py-2">Rule ID</th>
                <th className="text-right py-2">Count</th>
              </tr>
            </thead>
            <tbody>
              {stats.top_rules.map((r) => (
                <tr key={r.rule_id} className="border-b border-zinc-800/50">
                  <td className="py-2 font-mono text-zinc-300">{r.rule_id}</td>
                  <td className="py-2 text-right text-zinc-300">{r.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
