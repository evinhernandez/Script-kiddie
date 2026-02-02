"use client";
import { useEffect, useState } from "react";
import { apiGet, API_BASE } from "../../lib/api";

export default function SnippetsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      setItems(await apiGet("/snippets"));
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  async function openSnippet(item: any) {
    const lang = item.language;
    // path looks like "python/structured-output"
    const name = item.path.split("/")[1];
    const s = await apiGet(`/snippets/${lang}/${name}`);
    setSelected(s);
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="space-y-4">
      <h2 className="text-xl font-semibold">Snippets</h2>
      <p className="text-sm text-zinc-400">Secure copy/paste patterns for common AI/agent guardrails.</p>
      {err && <p className="text-sm text-red-300">{err}</p>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-1 space-y-2">
          {(items || []).map((it) => (
            <button
              key={it.id}
              onClick={() => openSnippet(it)}
              className="w-full text-left p-3 rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700"
            >
              <div className="font-medium">{it.title}</div>
              <div className="text-xs text-zinc-500">{it.language} • {(it.tags || []).join(", ")}</div>
            </button>
          ))}
          {(items || []).length === 0 && <p className="text-sm text-zinc-500">No snippets found.</p>}
        </div>

        <div className="md:col-span-2 p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
          {!selected && <p className="text-sm text-zinc-500">Pick a snippet on the left.</p>}
          {selected && (
            <div>
              <div className="flex justify-between items-start gap-3">
                <div>
                  <h3 className="text-lg font-semibold">{selected.meta.title}</h3>
                  <p className="text-sm text-zinc-400">{selected.meta.description}</p>
                </div>
              </div>
              <pre className="mt-4 text-xs bg-zinc-950 border border-zinc-800 rounded-xl p-3 overflow-x-auto whitespace-pre-wrap">
                {selected.content}
              </pre>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
