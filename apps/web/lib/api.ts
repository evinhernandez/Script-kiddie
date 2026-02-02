export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "dev-local-key";

export async function apiGet(path: string) {
  const r = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiPost(path: string, body: any) {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
