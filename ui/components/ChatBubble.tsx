"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Citations from "./Citations";
import type { ChatMessage } from "@/lib/types";

const REFUSAL = "I cannot find this in the provided documents";

interface ChatBubbleProps {
  message: ChatMessage;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";
  const isRefusal = !isUser && message.content.includes(REFUSAL);

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-br-sm bg-brand-600 text-white text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  // Loading skeleton
  if (message.isLoading) {
    return (
      <div className="flex gap-3">
        <BotAvatar />
        <div className="flex-1 max-w-[80%] space-y-2 pt-1">
          <div className="h-3 bg-[var(--border)] rounded animate-pulse w-3/4" />
          <div className="h-3 bg-[var(--border)] rounded animate-pulse w-1/2" />
          <div className="h-3 bg-[var(--border)] rounded animate-pulse w-2/3" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <BotAvatar />
      <div className="flex-1 max-w-[80%]">
        {/* Refusal badge */}
        {isRefusal && (
          <div className="flex items-center gap-2 mb-2 text-amber-400 text-xs font-medium">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
            </svg>
            Not found in documents
          </div>
        )}

        {/* Answer body */}
        <div
          className={`px-4 py-3 rounded-2xl rounded-bl-sm text-sm leading-relaxed prose-answer ${
            isRefusal
              ? "bg-amber-900/20 border border-amber-700/40 text-amber-200"
              : "bg-[var(--surface)] border border-[var(--border)] text-[var(--text)]"
          }`}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Citations */}
        {!isRefusal && message.sources && message.chunks && (
          <Citations sources={message.sources} chunks={message.chunks} />
        )}

        {/* Model badge */}
        {message.chunks && (
          <div className="mt-1.5 text-[10px] text-[var(--text-muted)]">
            {message.chunks.length} chunks retrieved
          </div>
        )}
      </div>
    </div>
  );
}

function BotAvatar() {
  return (
    <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-600/40 flex items-center justify-center shrink-0 mt-0.5">
      <svg className="w-4 h-4 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.5 2.121m-1.5-2.121L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-1.5-1.5m0 0l-3.75-3.75m3.75 3.75a2.25 2.25 0 01-2.25 2.25H9.75a2.25 2.25 0 01-2.25-2.25" />
      </svg>
    </div>
  );
}
