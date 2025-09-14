"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Citation = {
  source_file: string;
  page_start: number;
  page_end: number;
  score: number;
  snippet: string;
};

type AssistantMessage = {
  role: "assistant";
  content: string;
  citations: Citation[];
  prompt?: string;
};

type UserMessage = {
  role: "user";
  content: string;
};

type Message = AssistantMessage | UserMessage;

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [topK, setTopK] = useState<number>(6);
  const [maxTokens, setMaxTokens] = useState<number>(512);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  async function handleIngest() {
    try {
      setIngesting(true);
      const res = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_rebuild: true }),
      });
      const data = await res.json();
      alert(`Ingestion: ${data.message} (files=${data.files_processed}, chunks=${data.chunks_added})`);
    } catch (e) {
      console.error(e);
      alert("Ingestion failed - see console");
    } finally {
      setIngesting(false);
    }
  }

  async function handleSend() {
    if (!canSend) return;
    const question = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: topK, max_output_tokens: maxTokens }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const assistant: AssistantMessage = {
        role: "assistant",
        content: data.answer || "",
        citations: (data.citations || []) as Citation[],
        prompt: data.prompt,
      };
      setMessages((prev) => [...prev, assistant]);
    } catch (e: any) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${e.message || "failed"}`, citations: [] },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
      <header className="border-b border-neutral-800 px-4 py-3 flex items-center gap-3 sticky top-0 bg-neutral-950/80 backdrop-blur">
        <div className="font-semibold">Jharkhand Policies Chatbot</div>
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={handleIngest}
            disabled={ingesting}
            className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60"
            title="Rebuild the index from PDFs"
          >
            {ingesting ? "Ingesting…" : "Rebuild Index"}
          </button>
          <div className="flex items-center gap-2 text-sm">
            <label className="opacity-70">TopK</label>
            <input
              type="number"
              className="w-16 bg-neutral-900 border border-neutral-800 rounded px-2 py-1"
              value={topK}
              min={1}
              max={12}
              onChange={(e) => setTopK(parseInt(e.target.value || "6", 10))}
            />
          </div>
          <div className="flex items-center gap-2 text-sm">
            <label className="opacity-70">MaxTokens</label>
            <input
              type="number"
              className="w-20 bg-neutral-900 border border-neutral-800 rounded px-2 py-1"
              value={maxTokens}
              min={128}
              max={2048}
              onChange={(e) => setMaxTokens(parseInt(e.target.value || "512", 10))}
            />
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto max-w-4xl px-4 py-6">
        <div className="space-y-6">
          {messages.map((m, idx) => (
            <MessageBubble key={idx} message={m} />
          ))}
          {loading && (
            <div className="opacity-70 text-sm">Assistant is typing…</div>
          )}
          <div ref={endRef} />
        </div>
      </main>

      <footer className="border-t border-neutral-800 p-4">
        <div className="container mx-auto max-w-4xl">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask a question about Jharkhand policies…"
              className="flex-1 bg-neutral-900 border border-neutral-800 rounded px-3 py-2 outline-none focus:border-neutral-600"
            />
            <button
              onClick={handleSend}
              disabled={!canSend}
              className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-60"
            >
              Send
            </button>
          </div>
          <div className="mt-2 text-xs opacity-60">Backend: {API_BASE}</div>
        </div>
      </footer>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-600 text-white rounded-lg px-4 py-2 whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="w-full">
        <div className="max-w-[90%] bg-neutral-900 rounded-lg px-4 py-3 whitespace-pre-wrap">
          {message.content || ""}
        </div>
        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 border border-neutral-800 rounded">
            <div className="px-3 py-2 text-sm font-medium bg-neutral-900 border-b border-neutral-800">
              Citations ({message.citations.length})
            </div>
            <div className="divide-y divide-neutral-800">
              {message.citations.map((c, i) => (
                <div key={i} className="px-3 py-2 text-sm">
                  <div className="font-medium">
                    {c.source_file} (pp. {c.page_start}-{c.page_end}) — score {c.score.toFixed(3)}
                  </div>
                  {c.snippet && (
                    <div className="mt-1 opacity-80 line-clamp-3">{c.snippet}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        {/* Prompt view */}
        {message.prompt && <PromptViewer prompt={message.prompt} />}
      </div>
    </div>
  );
}

function PromptViewer({ prompt }: { prompt: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-xs px-2 py-1 rounded border border-neutral-800 hover:border-neutral-700"
      >
        {open ? "Hide Prompt" : "Show Prompt"}
      </button>
      {open && (
        <pre className="mt-2 text-xs overflow-auto max-h-72 bg-neutral-900 p-3 rounded border border-neutral-800 whitespace-pre-wrap">
{prompt}
        </pre>
      )}
    </div>
  );
}
