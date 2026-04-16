import type { QueryResponse, IngestResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function queryRAG(
  query: string,
  k: number = 5
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, k }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `API error ${res.status}`);
  }

  return res.json();
}

export async function ingestDocs(
  directory: string,
  strategy: "fixed" | "recursive" = "fixed",
  clearFirst: boolean = false
): Promise<IngestResponse> {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      directory,
      strategy,
      clear_first: clearFirst,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Ingest error ${res.status}`);
  }

  return res.json();
}

export async function getHealth(): Promise<{ status: string; vectors: number }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
