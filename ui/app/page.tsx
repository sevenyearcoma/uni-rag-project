import ChatInterface from "@/components/ChatInterface";

export default function Home() {
  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] px-6 py-3 flex items-center gap-3 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-brand-600/20 border border-brand-600/40 flex items-center justify-center">
          <svg className="w-5 h-5 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[var(--text)]">RAG Document QA</h1>
          <p className="text-[11px] text-[var(--text-muted)]">Grounded · Cited · Strict</p>
        </div>
      </header>

      {/* Chat */}
      <main className="flex-1 overflow-hidden max-w-4xl w-full mx-auto">
        <ChatInterface />
      </main>
    </div>
  );
}
