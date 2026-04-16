"use client";

import type { RetrievedChunk } from "@/lib/types";
import { useState } from "react";

interface CitationsProps {
  sources: string[];
  chunks: RetrievedChunk[];
}

export default function Citations({ sources, chunks }: CitationsProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-3 rounded-lg border border-[var(--border)] overflow-hidden text-sm">
      {/* Sources bar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-[var(--surface)]">
        <svg className="w-4 h-4 text-brand-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z" />
        </svg>
        <span className="text-[var(--text-muted)] font-medium">Sources:</span>
        <div className="flex flex-wrap gap-1.5">
          {sources.map((src) => (
            <span
              key={src}
              className="px-2 py-0.5 rounded bg-brand-700/30 text-brand-500 border border-brand-700/50 font-mono text-xs"
            >
              {src}
            </span>
          ))}
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="ml-auto text-[var(--text-muted)] hover:text-[var(--text)] transition-colors text-xs"
        >
          {expanded ? "Hide context" : `Show ${chunks.length} chunks`}
        </button>
      </div>

      {/* Expanded chunk view */}
      {expanded && (
        <div className="divide-y divide-[var(--border)]">
          {chunks.map((chunk, i) => (
            <div key={chunk.id} className="px-3 py-2.5">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-semibold text-[var(--text-muted)]">
                  [{i + 1}]
                </span>
                <span className="text-xs text-brand-500 font-mono">{chunk.metadata.filename}</span>
                <span className="text-xs text-[var(--text-muted)]">
                  chunk #{chunk.metadata.chunk_index}
                </span>
                <span className="text-xs text-[var(--text-muted)]">
                  {chunk.metadata.token_count} tok
                </span>
                <span className="ml-auto text-xs text-emerald-400">
                  {(chunk.score * 100).toFixed(1)}% match
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed line-clamp-4">
                {chunk.text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
