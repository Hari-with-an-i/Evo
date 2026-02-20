import { useState, useRef, useEffect } from "react";

const cx = (...cls) => cls.filter(Boolean).join(" ");

function parseStringItem(str) {
  const title = str.match(/Title:\s*(.+)/)?.[1]?.trim();
  const source = str.match(/Source:\s*(.+)/)?.[1]?.trim();
  const snippet = str.match(/Snippet:\s*([\s\S]+)/)?.[1]?.trim();
  const url = str.match(/https?:\/\/\S+/)?.[0];
  return { title, source, snippet, url };
}

// ── ChatBubble ────────────────────────────────────────────────────────────────
function ChatBubble({ data }) {
  return (
    <div className="flex gap-3 items-start">
      <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-base shrink-0">
        🤖
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-tl-sm rounded-tr-2xl rounded-br-2xl rounded-bl-2xl px-4 py-3 text-sm text-slate-200 leading-relaxed max-w-2xl">
        {data?.text || JSON.stringify(data)}
      </div>
    </div>
  );
}

// ── SentimentCard ─────────────────────────────────────────────────────────────
function SentimentCard({ data }) {
  const score =
    typeof data?.score === "number" ? data.score :
    typeof data?.sentiment_score === "number" ? data.sentiment_score : null;
  const label =
    data?.label || data?.sentiment ||
    (score !== null ? (score > 0 ? "Positive" : score < 0 ? "Negative" : "Neutral") : "Unknown");

  const isPositive = label?.toLowerCase().includes("positive");
  const isNegative = label?.toLowerCase().includes("negative");

  const colorClass = isPositive
    ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
    : isNegative
    ? "text-red-400 border-red-500/30 bg-red-500/10"
    : "text-amber-400 border-amber-500/30 bg-amber-500/10";

  const barColor = isPositive ? "bg-emerald-500" : isNegative ? "bg-red-500" : "bg-amber-400";
  const barWidth = score !== null ? `${Math.min(100, Math.abs(score) * 100)}%` : "50%";

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors">
      <h3 className="font-bold text-slate-200 text-xs mb-4 tracking-widest uppercase">📊 Sentiment Analysis</h3>
      <div className={cx("border rounded-lg p-4 flex flex-col items-center gap-2 mb-3", colorClass)}>
        <span className="text-2xl font-extrabold tracking-tight">{label}</span>
        {score !== null && <span className="text-xs opacity-70">Score: {score.toFixed ? score.toFixed(3) : score}</span>}
        <div className="w-full h-1.5 rounded-full bg-slate-700/50 mt-1">
          <div className={cx("h-full rounded-full", barColor)} style={{ width: barWidth }} />
        </div>
      </div>
      {data?.summary && <p className="text-slate-400 text-xs leading-relaxed">{data.summary}</p>}
      {data?.text && <p className="text-slate-500 text-xs italic mt-2 border-l-2 border-slate-600 pl-3">"{data.text}"</p>}
    </div>
  );
}

// ── GraphView ─────────────────────────────────────────────────────────────────
function GraphView({ data }) {
  const raw = Array.isArray(data?.results) ? data.results : Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : [];
  const items = raw.map((item) => (typeof item === "string" ? parseStringItem(item) : item));

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors">
      <h3 className="font-bold text-slate-200 text-xs mb-4 tracking-widest uppercase">📈 Trend Analysis</h3>
      {data?.timeframe && (
        <span className="inline-block text-xs bg-blue-500/15 text-blue-400 border border-blue-500/25 rounded-full px-3 py-0.5 mb-3">
          {data.timeframe}
        </span>
      )}
      {data?.query && <p className="text-slate-500 text-xs mb-3">Query: {data.query}</p>}
      {items.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {items.map((item, i) => (
            <li key={i} className="bg-slate-900/60 border border-slate-700/60 rounded-lg p-3 flex flex-col gap-1">
              {item.title && <strong className="text-slate-200 text-sm">{item.title}</strong>}
              {item.source && (
                <span className="inline-block text-[10px] bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 rounded-full px-2 py-0.5 w-fit">
                  {item.source}
                </span>
              )}
              {item.snippet && <p className="text-slate-400 text-xs leading-relaxed">{item.snippet}</p>}
              {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="text-blue-400 text-[10px] hover:underline break-all">{item.url}</a>}
            </li>
          ))}
        </ul>
      ) : (
        <pre className="text-slate-500 text-[10px] bg-slate-900/60 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap break-all">{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  );
}

// ── ReportView ────────────────────────────────────────────────────────────────
function ReportView({ data }) {
  const report =
    typeof data === "string" ? data :
    data?.report || data?.narrative || data?.content || JSON.stringify(data, null, 2);

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors col-span-full">
      <h3 className="font-bold text-slate-200 text-xs mb-4 tracking-widest uppercase">📋 Narrative Report</h3>
      <div className="flex flex-col gap-2 max-h-96 overflow-y-auto pr-1">
        {String(report).split("\n").map((line, i) =>
          line.startsWith("#") ? (
            <p key={i} className="text-indigo-300 font-bold text-sm mt-2">{line.replace(/^#+\s*/, "")}</p>
          ) : line.trim() === "" ? null : (
            <p key={i} className="text-slate-300 text-sm leading-relaxed">{line}</p>
          )
        )}
      </div>
    </div>
  );
}

// ── CounterspeechCard ─────────────────────────────────────────────────────────
// Handles the backend shape: { type, content, evidence: [{index, title, source, date, url, snippet}] }
function CounterspeechCard({ data }) {
  const content = data?.content || data?.text || null;
  const evidence = Array.isArray(data?.evidence) ? data.evidence : [];

  // Fallback for plain array shapes
  const points =
    !content && evidence.length === 0
      ? (Array.isArray(data?.arguments) ? data.arguments :
         Array.isArray(data?.counterspeech) ? data.counterspeech :
         Array.isArray(data) ? data : [])
      : [];

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors col-span-full">
      <h3 className="font-bold text-slate-200 text-xs mb-4 tracking-widest uppercase">🛡️ Counterspeech</h3>

      {/* Optional claim label */}
      {data?.claim && (
        <div className="border-l-2 border-amber-500 bg-amber-500/5 rounded-r-lg px-3 py-2 mb-4 text-xs text-amber-200 italic">
          Claim: "{data.claim}"
        </div>
      )}

      {/* Main debunking paragraph */}
      {content && (
        <p className="text-slate-300 text-sm leading-relaxed mb-5">{content}</p>
      )}

      {/* Evidence articles */}
      {evidence.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-3">Supporting Evidence</p>
          <ul className="flex flex-col gap-2">
            {evidence.map((ev, i) => (
              <li key={i} className="bg-slate-900/60 border border-slate-700/60 rounded-lg p-3 flex flex-col gap-1">
                <div className="flex items-start justify-between gap-2 flex-wrap">
                  {ev.title && <strong className="text-slate-200 text-sm leading-snug">{ev.title}</strong>}
                  {ev.source && (
                    <span className="shrink-0 inline-block text-[10px] bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 rounded-full px-2 py-0.5">
                      {ev.source}
                    </span>
                  )}
                </div>
                {ev.snippet && <p className="text-slate-400 text-xs leading-relaxed">{ev.snippet}</p>}
                <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                  {ev.date && <span className="text-slate-600 text-[10px]">{ev.date}</span>}
                  {ev.url && (
                    <a href={ev.url} target="_blank" rel="noreferrer" className="text-blue-400 text-[10px] hover:underline break-all">
                      {ev.url}
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Fallback: plain numbered list */}
      {points.length > 0 && (
        <ol className="flex flex-col gap-3">
          {points.map((pt, i) => (
            <li key={i} className="flex gap-3 items-start">
              <span className="shrink-0 w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold flex items-center justify-center border border-emerald-500/30">
                {i + 1}
              </span>
              <span className="text-slate-300 text-sm leading-relaxed">
                {typeof pt === "string" ? pt : JSON.stringify(pt)}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

// ── ResearchFeed ──────────────────────────────────────────────────────────────
function ResearchFeed({ data }) {
  const raw = Array.isArray(data?.results) ? data.results :
              Array.isArray(data?.articles) ? data.articles :
              Array.isArray(data) ? data : [];

  const items = raw.map((item) => (typeof item === "string" ? parseStringItem(item) : item));

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors">
      <h3 className="font-bold text-slate-200 text-xs mb-4 tracking-widest uppercase">🔍 Research Feed</h3>
      {data?.query && <p className="text-slate-500 text-xs mb-3">Query: {data.query}</p>}
      {items.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {items.map((item, i) => (
            <li key={i} className="bg-slate-900/60 border border-slate-700/60 rounded-lg p-3 flex flex-col gap-1.5">
              {item.title && <strong className="text-slate-200 text-sm leading-snug">{item.title}</strong>}
              {item.source && (
                <span className="inline-block text-[10px] bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 rounded-full px-2 py-0.5 w-fit">
                  {item.source}
                </span>
              )}
              {item.snippet && <p className="text-slate-400 text-xs leading-relaxed">{item.snippet}</p>}
              {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="text-blue-400 text-[10px] hover:underline break-all">{item.url}</a>}
            </li>
          ))}
        </ul>
      ) : (
        <pre className="text-slate-500 text-[10px] bg-slate-900/60 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap break-all">{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  );
}

// ── GenericCard (fallback) ────────────────────────────────────────────────────
function GenericCard({ title, data }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5">
      <h3 className="font-bold text-slate-200 text-xs mb-3 uppercase tracking-widest">{title}</h3>
      <pre className="text-slate-500 text-[10px] bg-slate-900/60 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap break-all">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

// ── Component map ─────────────────────────────────────────────────────────────
const COMPONENT_MAP = {
  ChatBubble,
  SentimentCard,
  GraphView,
  ReportView,
  CounterspeechCard,
  ReseachFeed: ResearchFeed, // intentional backend typo
  ResearchFeed,
};

function ResponseRenderer({ response }) {
  if (!response) return null;
  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))" }}>
      {Object.entries(response).map(([key, block]) => {
        const Comp = COMPONENT_MAP[block?.component];
        if (!Comp) return <GenericCard key={key} title={key} data={block?.data} />;
        return <Comp key={key} data={block.data} />;
      })}
    </div>
  );
}

function LoadingCard() {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4 flex items-center gap-4 w-fit">
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <span key={i} className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
        ))}
      </div>
      <p className="text-slate-400 text-sm">Agent is thinking &amp; calling tools…</p>
    </div>
  );
}

const EXAMPLES = [
  "Is the claim that 5G causes disease spreading online?",
  "Analyze sentiment of vaccine misinformation tweets",
  "Generate a full report on flat-earth conspiracy theories",
  "Debunk: 'The moon landing was faked'",
];

const NAV_ITEMS = [
  { icon: "🔍", label: "Research & Scout" },
  { icon: "📈", label: "Trend Analysis" },
  { icon: "📊", label: "Sentiment" },
  { icon: "🛡️", label: "Counterspeech" },
  { icon: "📋", label: "Full Report" },
];

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const submit = async () => {
    const query = input.trim();
    if (!query || loading) return;
    setInput("");
    setError(null);
    setHistory((h) => [...h, { role: "user", content: query }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/brain/invoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: query }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const json = await res.json();

      let data;
      try {
        const parsed = JSON.parse(json.final_response);
        // Strip null/undefined top-level keys (e.g. debug_info: null)
        data = Object.fromEntries(
          Object.entries(parsed).filter(([, v]) => v !== null && v !== undefined)
        );
      } catch {
        data = { agent_response: { component: "ChatBubble", data: { text: json.final_response } } };
      }

      setHistory((h) => [...h, { role: "assistant", response: data }]);
    } catch (e) {
      setError(e.message);
      setHistory((h) => [
        ...h,
        { role: "assistant", response: { agent_response: { component: "ChatBubble", data: { text: `Error: ${e.message}` } } } },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200 overflow-hidden">

      {/* Sidebar */}
      <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col py-6 px-4 gap-6">
        <div className="flex items-center gap-2.5 pb-5 border-b border-slate-800">
          <span className="text-2xl">💬</span>
          <span className="text-lg font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Evo
          </span>
        </div>
        <nav className="flex flex-col gap-1 flex-1">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2 px-2">Capabilities</p>
          {NAV_ITEMS.map(({ icon, label }) => (
            <div key={label} className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-400 text-[13px] hover:bg-slate-800 hover:text-slate-200 transition-colors cursor-default">
              <span>{icon}</span><span>{label}</span>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main */}
      <main className="flex flex-col flex-1 overflow-hidden">

        {/* Topbar */}
        <header className="flex items-center justify-between px-7 py-4 border-b border-slate-800 bg-slate-900 shrink-0">
          <h1 className="font-bold text-[15px] tracking-wide text-slate-100">Misinformation Mitigation Assistant</h1>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            <span className="text-xs text-slate-500">Online</span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-7 py-8 flex flex-col gap-6">
          {history.length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 text-center gap-5">
              <div className="text-5xl">🧠</div>
              <div>
                <h2 className="text-xl font-bold text-slate-100 mb-2">What would you like to investigate?</h2>
                <p className="text-slate-500 text-sm leading-relaxed max-w-md">
                  Ask me to scout a topic, analyze trends, check sentiment, or generate a full counter-narrative report.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center mt-2">
                {EXAMPLES.map((ex) => (
                  <button key={ex} onClick={() => setInput(ex)}
                    className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-blue-500/50 text-slate-300 text-xs px-4 py-2 rounded-full transition-all cursor-pointer">
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {history.map((msg, i) =>
            msg.role === "user" ? (
              <div key={i} className="flex justify-end">
                <div className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white text-sm px-4 py-3 rounded-[18px_18px_4px_18px] max-w-lg leading-relaxed shadow-lg">
                  {msg.content}
                </div>
              </div>
            ) : (
              <div key={i}><ResponseRenderer response={msg.response} /></div>
            )
          )}

          {loading && <div><LoadingCard /></div>}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-7 pb-6 pt-4 border-t border-slate-800 bg-slate-900 shrink-0">
          {error && (
            <div className="mb-3 bg-red-500/10 border border-red-500/25 text-red-300 text-xs px-4 py-2 rounded-lg">⚠ {error}</div>
          )}
          <div className="flex gap-3 items-end bg-slate-800 border border-slate-700 focus-within:border-blue-500/60 rounded-xl px-4 py-3 transition-colors">
            <textarea
              className="flex-1 bg-transparent border-none outline-none text-slate-200 text-sm leading-relaxed resize-none placeholder:text-slate-500"
              placeholder="Ask about misinformation, request a report, or check a claim…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              rows={2}
            />
            <button onClick={submit} disabled={loading || !input.trim()}
              className={cx(
                "w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold transition-all shrink-0",
                loading || !input.trim()
                  ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                  : "bg-gradient-to-br from-blue-500 to-indigo-500 text-white hover:opacity-90 hover:scale-105 shadow-md cursor-pointer"
              )}>
              {loading ? "⏳" : "↑"}
            </button>
          </div>
          <p className="text-[11px] text-slate-600 mt-2 pl-1">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </main>
    </div>
  );
}