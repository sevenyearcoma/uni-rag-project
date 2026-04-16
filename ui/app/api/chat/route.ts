/**
 * Next.js API route — proxies queries to the Python FastAPI backend.
 * Keeps the backend URL server-side only (not exposed to the browser).
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const upstream = await fetch(`${BACKEND}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      return NextResponse.json(data, { status: upstream.status });
    }

    return NextResponse.json(data);
  } catch (err) {
    console.error("[/api/chat]", err);
    return NextResponse.json(
      { detail: "Failed to reach the RAG backend. Is it running?" },
      { status: 502 }
    );
  }
}
