"use client";

import { useEffect, useMemo, useRef, useState } from "react";

// --- TYPE DEFINITIONS ---
type Citation = {
  source_file: string;
  page_start: number;
  page_end: number;
  score: number;
  snippet: string;
};

type RoutingInfo = {
  primary_server: string;
  fallback_server?: string;
  complexity: string;
  confidence: number;
  fallback_used: boolean;
  fallback_reason?: string;
};

type AssistantMessage = {
  role: "assistant";
  content: string;
  citations: Citation[];
  routing_info?: RoutingInfo;
  prompt?: string;
};

type UserMessage = {
  role: "user";
  content: string;
};

type Message = AssistantMessage | UserMessage;

type ServerStatus = {
  name: string;
  port: number;
  description: string;
  running: boolean;
  health: any;
};

type SystemStatus = {
  timestamp: number;
  servers: Record<string, ServerStatus>;
  overall_health: string;
  healthy_count: number;
  total_count: number;
};

// Use a more descriptive name for the orchestrator's base URL
const ORCHESTRATOR_BASE_URL = "http://localhost:8000";

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [selectedServer, setSelectedServer] = useState<string>("auto");
  const [topK, setTopK] = useState<number>(5);
  const [maxTokens, setMaxTokens] = useState<number>(512);
  const [showSystemStatus, setShowSystemStatus] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  // Fetch consolidated system health from a dedicated orchestrator endpoint
  async function fetchSystemStatus() {
    try {
      const res = await fetch(`${ORCHESTRATOR_BASE_URL}/system/health`);
      if (res.ok) {
        const data: SystemStatus = await res.json();
        setSystemStatus(data);
      } else {
        setSystemStatus(null);
        console.error("Failed to fetch system status:", res.statusText);
      }
    } catch (e) {
      console.error("Failed to fetch system status:", e);
      setSystemStatus(null);
    }
  }

  // Remove frontend fallback logic. Only call the orchestrator.
  async function handleIngest() {
    try {
      setIngesting(true);
      const res = await fetch(`${ORCHESTRATOR_BASE_URL}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_rebuild: true }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Ingestion request failed");
      }
      
      const data = await res.json();
      alert(`Ingestion: ${data.message || 'Success'} (files=${data.files_processed || 'N/A'}, chunks=${data.chunks_added || 'N/A'})`);

    } catch (e: any) {
      console.error(e);
      alert(`Ingestion failed: ${e.message}`);
    } finally {
      setIngesting(false);
      fetchSystemStatus(); // Refresh status after ingestion
    }
  }
  
  // Refactor query to use a stable endpoint and send routing hints in the body
  async function handleSend() {
    if (!canSend) return;
    const question = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    
    try {
      const url = `${ORCHESTRATOR_BASE_URL}/query`;
      const requestBody = {
        question,
        top_k: topK,
        max_output_tokens: maxTokens,
        ...(selectedServer !== "auto" && { target_server: selectedServer }),
      };

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `HTTP Error ${res.status}`);
      }
      
      const data = await res.json();
      const assistant: AssistantMessage = {
        role: "assistant",
        content: data.answer || "",
        citations: (data.citations || []) as Citation[],
        routing_info: data.routing_info,
        prompt: data.prompt,
      };
      setMessages((prev) => [...prev, assistant]);

    } catch (e: any) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: `Error: ${e.message || "Failed to connect to the server."}`, 
          citations: [] 
        },
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 flex flex-col">
      <header className="border-b border-slate-700 px-4 py-4 flex items-center gap-4 sticky top-0 bg-slate-900/80 backdrop-blur-lg z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <div>
            <div className="font-bold text-lg">Multi-Level Summarization</div>
            <div className="text-sm text-slate-400">Jharkhand Policies AI</div>
          </div>
        </div>
        
        <div className="ml-auto flex items-center gap-4">
          <button
            onClick={() => setShowSystemStatus(!showSystemStatus)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              systemStatus?.overall_health === "healthy" 
                ? "bg-green-600 hover:bg-green-500" 
                : systemStatus?.overall_health === "degraded"
                ? "bg-yellow-600 hover:bg-yellow-500"
                : "bg-red-600 hover:bg-red-500"
            }`}
          >
            {systemStatus ? `${systemStatus.healthy_count}/${systemStatus.total_count} Servers Online` : "System Offline"}
          </button>
          
          <select
            value={selectedServer}
            onChange={(e) => setSelectedServer(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm"
          >
            <option value="auto">🤖 Auto Route</option>
            <option value="server1">📄 Server 1 (Full Docs)</option>
            <option value="server2">📝 Server 2 (L2 Summary)</option>
            <option value="server3">📋 Server 3 (L3 Summary)</option>
          </select>
          
          <button
            onClick={handleIngest}
            disabled={ingesting}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-sm font-medium transition-colors"
          >
            {ingesting ? "🔄 Processing..." : "📚 Ingest Docs"}
          </button>
        </div>
      </header>

      {showSystemStatus && (
        <div className="bg-slate-800 border-b border-slate-700 p-4">
          <div className="container mx-auto max-w-6xl">
            {systemStatus ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {Object.entries(systemStatus.servers).map(([name, server]) => (
                  <div key={name} className="bg-slate-700 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-3 h-3 rounded-full ${server.running ? 'bg-green-400' : 'bg-red-400'}`}></div>
                      <span className="font-medium text-sm">{server.name}</span>
                    </div>
                    <div className="text-xs text-slate-400">{server.description}</div>
                    {server.health?.stats && (
                      <div className="mt-2 text-xs">
                        <div>Vectors: {server.health.stats.vectors}</div>
                        <div>Files: {server.health.stats.files_indexed}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-slate-400">Could not retrieve system status.</div>
            )}
          </div>
        </div>
      )}
      
      <main className="flex-1 container mx-auto max-w-5xl px-4 py-6">
        <div className="space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                <span className="text-white text-2xl">🤖</span>
              </div>
              <h2 className="text-2xl font-bold mb-2">Welcome to Multi-Level Summarization</h2>
              <p className="text-slate-400 mb-6 max-w-2xl mx-auto">
                Ask questions about Jharkhand policies. The system will intelligently route your query 
                to the most appropriate summarization level for optimal results.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-blue-400 font-semibold mb-2">📄 Detailed Queries</div>
                  <div className="text-sm text-slate-400">"What are the specific requirements in section 4.2?"</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-green-400 font-semibold mb-2">📝 Summary Queries</div>
                  <div className="text-sm text-slate-400">"Give me a summary of MSME policy"</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-purple-400 font-semibold mb-2">📋 Key Points</div>
                  <div className="text-sm text-slate-400">"What are the key points about policies?"</div>
                </div>
              </div>
            </div>
          )}
          
          {messages.map((m, idx) => (
            <MessageBubble key={idx} message={m} />
          ))}
          
          {loading && (
            <div className="flex items-center gap-2 text-slate-400">
              <div className="animate-spin w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full"></div>
              <span>AI is analyzing your query...</span>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </main>

      <footer className="border-t border-slate-700 p-4 bg-slate-900/50">
        <div className="container mx-auto max-w-5xl">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask about Jharkhand policies..."
              className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            />
            <button
              onClick={handleSend}
              disabled={!canSend}
              className="px-6 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:opacity-60 font-medium transition-all"
            >
              Send
            </button>
          </div>
          
          <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
            <div>Backend: {ORCHESTRATOR_BASE_URL}</div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <label>Top-K:</label>
                <input
                  type="number"
                  className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs"
                  value={topK}
                  min={1}
                  max={12}
                  onChange={(e) => setTopK(parseInt(e.target.value || "5", 10))}
                />
              </div>
              <div className="flex items-center gap-2">
                <label>Max Tokens:</label>
                <input
                  type="number"
                  className="w-20 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs"
                  value={maxTokens}
                  min={128}
                  max={2048}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value || "512", 10))}
                />
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// --- SUB-COMPONENTS & HELPERS ---

function MessageBubble({ message }: { message: Message }) {
  // Handle user messages
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-2xl px-6 py-4 shadow-lg">
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>
      </div>
    );
  }

  // Handle assistant messages
  return (
    <div className="flex justify-start">
      <div className="w-full">
        {message.routing_info && (
          <div className="mb-3 flex items-center gap-2 text-sm">
            <div className={`px-2 py-1 rounded-full text-xs font-medium text-white ${getServerColor(message.routing_info.primary_server)}`}>
              {message.routing_info.primary_server}
            </div>
            <span className={`font-medium ${getComplexityColor(message.routing_info.complexity)}`}>
              {message.routing_info.complexity}
            </span>
            <span className="text-slate-500">
              (confidence: {(message.routing_info.confidence * 100).toFixed(0)}%)
            </span>
            {message.routing_info.fallback_used && (
              <span className="text-yellow-400 text-xs">⚠️ Fallback used</span>
            )}
          </div>
        )}
        
        <div className="max-w-[90%] bg-slate-800 rounded-2xl px-6 py-4 shadow-lg border border-slate-700">
          <div className="whitespace-pre-wrap">{message.content || ""}</div>
        </div>
        
        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 max-w-[90%]">
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              <div className="px-4 py-3 text-sm font-semibold bg-slate-700 border-b border-slate-600 flex items-center gap-2">
                <span>📚</span>
                <span>Sources ({message.citations.length})</span>
              </div>
              <div className="divide-y divide-slate-700">
                {message.citations.map((c, i) => (
                  <div key={i} className="px-4 py-3 text-sm">
                    <div className="font-medium text-blue-400 mb-1">
                      {c.source_file} (pages {c.page_start}-{c.page_end})
                    </div>
                    <div className="text-slate-400 text-xs mb-2">
                      Relevance: {(c.score * 100).toFixed(1)}%
                    </div>
                    {c.snippet && (
                      <div className="text-slate-300 bg-slate-900 rounded-lg p-3 text-xs leading-relaxed">
                        {c.snippet}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {message.prompt && <PromptViewer prompt={message.prompt} />}
      </div>
    </div>
  );
}

function PromptViewer({ prompt }: { prompt: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-3 max-w-[90%]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-xs px-3 py-2 rounded-lg border border-slate-600 hover:border-slate-500 bg-slate-800 hover:bg-slate-700 transition-colors"
      >
        {open ? "🔽 Hide Prompt" : "🔼 Show Prompt"}
      </button>
      {open && (
        <pre className="mt-3 text-xs overflow-auto max-h-80 bg-slate-900 p-4 rounded-lg border border-slate-700 whitespace-pre-wrap leading-relaxed">
          {prompt}
        </pre>
      )}
    </div>
  );
}

function getServerColor(server: string) {
  switch (server) {
    case "server1": return "bg-blue-500";
    case "server2": return "bg-green-500";
    case "server3": return "bg-purple-500";
    case "orchestrator": return "bg-orange-500";
    default: return "bg-gray-500";
  }
}

function getComplexityColor(complexity: string) {
  switch (complexity) {
    case "simple": return "text-green-400";
    case "moderate": return "text-yellow-400";
    case "detailed": return "text-blue-400";
    case "comprehensive": return "text-red-400";
    default: return "text-gray-400";
  }
}

