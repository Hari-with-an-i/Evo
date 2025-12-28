import React, { useState, useRef, useEffect } from "react";
import {
  Menu,
  Plus,
  Send,
  User,
  Bot,
  Loader2,
  Sun,
  Moon,
  FileText,
  TrendingUp,
  ShieldAlert,
  Info
} from "lucide-react";

// --- CHART IMPORTS ---
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";

// --- REGISTER CHARTJS COMPONENTS ---
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// --- SENTIMENT CHART COMPONENT (Integrated) ---
function SentimentChart({ analyticsData }) {
  if (!analyticsData || Object.keys(analyticsData).length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-gray-400 text-sm border border-dashed border-gray-600 rounded-lg">
        <TrendingUp size={24} className="mb-2 opacity-50" />
        No sentiment data available to display.
      </div>
    );
  }

  const labels = Object.keys(analyticsData).sort();
  const dataPoints = labels.map(
    (label) => analyticsData[label].average_sentiment_score
  );

  const data = {
    labels,
    datasets: [
      {
        label: "Average Sentiment Trend",
        data: dataPoints,
        borderColor: "#4dabf7",
        backgroundColor: "rgba(77, 171, 247, 0.4)",
        tension: 0.3,
        pointBackgroundColor: "#fff",
        pointBorderColor: "#4dabf7",
        pointHoverBackgroundColor: "#4dabf7",
        pointHoverBorderColor: "#fff",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false, // Allows the chart to fill container height
    animation: {
      duration: 900,
      easing: "easeOutQuart",
    },
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#9ca3af", // Tailwind gray-400
        }
      },
      title: { display: false },
    },
    scales: {
      y: {
        min: -1,
        max: 1,
        grid: {
          color: "rgba(255, 255, 255, 0.1)",
        },
        ticks: {
          color: "#9ca3af",
        }
      },
      x: {
        grid: {
          color: "rgba(255, 255, 255, 0.1)",
        },
        ticks: {
          color: "#9ca3af",
        }
      }
    },
  };

  return (
    <div className="h-64 w-full">
      <Line options={options} data={data} />
    </div>
  );
}

// --- MAIN CHAT INTERFACE ---
export default function ChatInterface() {
  const [selectedTool, setSelectedTool] = useState("counterspeech");
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: "Hello! I'm Evo. How can I help you today?",
      type: "text",
    },
  ]);

  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  
  const [conversations, setConversations] = useState([
    { id: 1, title: "New conversation", active: true },
  ]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // ============================================================
  //                      HANDLE SEND
  // ============================================================
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: messages.length + 1,
      role: "user",
      content: input,
      type: "text",
    };

    setMessages((prev) => [...prev, userMessage]);
    const query = input;
    setInput("");
    setIsLoading(true); // START LOADING

    // Choose endpoint
    let endpoint = "";
    if (selectedTool === "counterspeech") {
      endpoint = "http://127.0.0.1:8000/generate-counterspeech";
    } else if (selectedTool === "perception") {
      endpoint = "http://127.0.0.1:8000/analyze-perception-trend";
    }

    // Prepare request body
    let requestBody = {};
    if (selectedTool === "counterspeech") {
      requestBody = { statement: query, days_back: 30, top_k: 3 };
    } else if (selectedTool === "perception") {
      requestBody = { keywords: query, time_period_days: 30, granularity_days: 7 };
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      let content = "";
      let evidences = [];
      let sentimentData = null;
      let reportData = null; 

      // -------- COUNTERSPEECH --------
      if (selectedTool === "counterspeech") {
        content = data?.result?.counterspeech || "No counterspeech generated.";
        evidences = data?.result?.evidences || [];
      }

      // -------- PERCEPTION TREND ANALYSIS --------
      if (selectedTool === "perception") {
        const report = data?.report;
        reportData = report; 
        content = "Here is the perception trend analysis based on your query."; 

        sentimentData = data?.time_series_analytics || {};
        evidences = sentimentData; // Re-using evidences field for raw data lists
      }

      const aiMessage = {
        id: messages.length + 2,
        role: "assistant",
        content,
        evidences,
        sentimentData,
        reportData, 
        type: selectedTool === "perception" && reportData ? "perception_report" : "text"
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
      
      // --- DEMO FALLBACK FOR PREVIEW PURPOSES ---
      setTimeout(() => {
        const isPerception = selectedTool === "perception";
        
        // Mock data for graph visualization
        const mockAnalytics = {
            "2023-10-01": { average_sentiment_score: 0.5, dominant_topics: ["AI", "Tech"] },
            "2023-10-08": { average_sentiment_score: 0.2, dominant_topics: ["Privacy", "Security"] },
            "2023-10-15": { average_sentiment_score: -0.4, dominant_topics: ["Leaks", "Data"] },
            "2023-10-22": { average_sentiment_score: -0.1, dominant_topics: ["Patch", "Update"] },
            "2023-10-29": { average_sentiment_score: 0.3, dominant_topics: ["Trust", "Recovery"] },
        };

        const mockMessage = {
          id: messages.length + 2,
          role: "assistant",
          type: isPerception ? "perception_report" : "text",
          content: isPerception ? "Analysis complete." : "Here is a counter speech argument...",
          reportData: isPerception ? {
            executive_summary: "The perception of this topic has shifted significantly over the last 30 days.",
            analysis_of_trend: "Overall positive trend initially, followed by a dip due to security concerns.",
            mitigation_strategies: [
              { name: "Transparency Campaign", description: "Release full datasets.", justification: "Rebuilds trust." },
            ]
          } : null,
          sentimentData: isPerception ? mockAnalytics : null,
          evidences: isPerception ? mockAnalytics : []
        };
        
        // UNCOMMENT THIS LINE TO TEST UI WITH MOCK DATA IF SERVER IS DOWN:
        // setMessages((prev) => [...prev, mockMessage]); 
        
        const errorMsg = {
           id: messages.length + 2,
           role: "assistant",
           type: "text",
           content: "⚠️ Could not connect to backend (http://127.0.0.1:8000). Ensure the server is running."
        };
        setMessages((prev) => [...prev, errorMsg]);
      }, 1000);
    } finally {
      setIsLoading(false); 
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewChat = () => {
    const newConv = {
      id: conversations.length + 1,
      title: "New conversation",
      active: true,
    };
    setConversations((prev) =>
      prev.map((c) => ({ ...c, active: false })).concat(newConv)
    );
    setMessages([
      { id: 1, role: "assistant", content: "Hello! How can I help you today?", type: "text" },
    ]);
  };

  // ============================================================
  //                  THEME & STYLE HELPERS
  // ============================================================
  const themeClasses = {
    bg: isDarkMode ? "bg-gray-900" : "bg-gray-50",
    sidebarBg: isDarkMode ? "bg-gray-950" : "bg-white",
    sidebarHover: isDarkMode ? "hover:bg-gray-800" : "hover:bg-gray-100",
    sidebarActive: isDarkMode ? "bg-gray-800" : "bg-gray-200",
    text: isDarkMode ? "text-white" : "text-gray-900",
    subText: isDarkMode ? "text-gray-400" : "text-gray-500",
    border: isDarkMode ? "border-gray-700" : "border-gray-200",
    inputBg: isDarkMode ? "bg-gray-800" : "bg-white",
    inputBorder: isDarkMode ? "border-gray-600" : "border-gray-300",
    botMsgBg: isDarkMode ? "bg-gray-800/50" : "bg-white border border-gray-200 shadow-sm",
    userMsgBg: isDarkMode ? "bg-transparent" : "bg-transparent",
    cardBg: isDarkMode ? "bg-gray-800/60" : "bg-white shadow-sm border border-gray-100",
  };

  const normalizeText = (section) => {
    if (!section) return "No data";
    if (section?.summary) return section.summary;
    if (typeof section === "string") return section;
    if (typeof section === "object") {
      return Object.entries(section)
        .map(([key, value]) => `• ${key}: ${normalizeText(value)}`)
        .join("\n");
    }
    return String(section);
  };

  // ============================================================
  //                  RENDER UI
  // ============================================================
  return (
    <div className={`flex h-screen ${themeClasses.bg} ${themeClasses.text} transition-colors duration-300`}>
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } transition-all duration-300 ${themeClasses.sidebarBg} border-r ${themeClasses.border} flex flex-col overflow-hidden`}
      >
        <div className="p-3">
          <button
            onClick={startNewChat}
            className={`flex items-center gap-3 w-full p-3 rounded-lg border ${themeClasses.border} ${themeClasses.sidebarHover} transition-colors`}
          >
            <Plus size={18} />
            <span className="font-medium">New chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`p-3 rounded-lg mb-1 cursor-pointer ${themeClasses.sidebarHover} transition-colors ${
                conv.active ? themeClasses.sidebarActive : ""
              }`}
            >
              <div className="text-sm truncate font-medium">{conv.title}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className={`border-b ${themeClasses.border} p-4 flex items-center justify-between`}>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`p-2 rounded-lg transition-colors ${themeClasses.sidebarHover}`}
            >
              <Menu size={20} />
            </button>
            <h1 className="text-lg font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
              Evo
            </h1>
          </div>
          
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className={`p-2 rounded-full transition-colors ${themeClasses.sidebarHover} border ${themeClasses.border}`}
          >
            {isDarkMode ? <Sun size={18} className="text-yellow-400" /> : <Moon size={18} className="text-slate-600" />}
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-4xl mx-auto px-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 py-8 ${
                  message.role === "assistant" ? themeClasses.botMsgBg : themeClasses.userMsgBg
                } ${message.role === "assistant" && !isDarkMode ? "px-4 my-2 rounded-xl" : ""}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === "user" ? "bg-gray-500" : "bg-indigo-600"
                } text-white`}>
                  {message.role === "user" ? <User size={18} /> : <Bot size={18} />}
                </div>

                <div className="flex-1 pt-1 min-w-0">
                  <div className={`prose max-w-none ${isDarkMode ? "prose-invert" : ""}`}>
                    
                    {/* --- RENDER PERCEPTION REPORT (FANCY HEADINGS) --- */}
                    {message.type === "perception_report" && message.reportData ? (
                      <div className="space-y-6">
                        
                        {/* Executive Summary */}
                        <div className={`rounded-xl border-l-4 border-indigo-500 overflow-hidden ${themeClasses.cardBg}`}>
                          <div className={`px-4 py-3 border-b ${themeClasses.border} flex items-center gap-2 bg-indigo-500/10`}>
                             <FileText size={18} className="text-indigo-400" />
                             <h3 className="font-bold text-lg m-0 text-indigo-400">Executive Summary</h3>
                          </div>
                          <div className="p-4 whitespace-pre-line text-sm leading-relaxed opacity-90">
                            {normalizeText(message.reportData.executive_summary)}
                          </div>
                        </div>

                        {/* Analysis of Trend */}
                        <div className={`rounded-xl border-l-4 border-emerald-500 overflow-hidden ${themeClasses.cardBg}`}>
                          <div className={`px-4 py-3 border-b ${themeClasses.border} flex items-center gap-2 bg-emerald-500/10`}>
                             <TrendingUp size={18} className="text-emerald-400" />
                             <h3 className="font-bold text-lg m-0 text-emerald-400">Analysis of Trend</h3>
                          </div>
                          <div className="p-4 whitespace-pre-line text-sm leading-relaxed opacity-90">
                            {normalizeText(message.reportData.analysis_of_trend)}
                          </div>
                        </div>

                        {/* Strategies */}
                        <div className={`rounded-xl border-l-4 border-amber-500 overflow-hidden ${themeClasses.cardBg}`}>
                           <div className={`px-4 py-3 border-b ${themeClasses.border} flex items-center gap-2 bg-amber-500/10`}>
                             <ShieldAlert size={18} className="text-amber-400" />
                             <h3 className="font-bold text-lg m-0 text-amber-400">Recommended Strategies</h3>
                           </div>
                           <div className="p-4 space-y-4">
                              {Array.isArray(message.reportData.mitigation_strategies) ? (
                                message.reportData.mitigation_strategies.map((s, idx) => (
                                <div key={idx} className={`p-3 rounded border ${themeClasses.border} bg-opacity-50`}>
                                   <div className="font-bold text-amber-400/90 mb-1">{s.name}</div>
                                   <div className="text-sm opacity-90 mb-2">{s.description}</div>
                                   <div className="text-xs italic opacity-70 border-t border-gray-600/30 pt-2 mt-2">
                                     Rationale: {s.justification}
                                   </div>
                                </div>
                              ))
                              ) : (
                                <div className="text-sm opacity-90 whitespace-pre-line">
                                  {normalizeText(message.reportData.mitigation_strategies)}
                                </div>
                              )}
                           </div>
                        </div>

                      </div>
                    ) : (
                      <p style={{ whiteSpace: "pre-line" }}>{message.content}</p>
                    )}


                    {/* --- SENTIMENT CHART (NOW REAL) --- */}
                    {message.sentimentData && selectedTool === "perception" && (
                      <div className={`mt-6 mb-6 p-4 rounded-xl border ${themeClasses.border} ${themeClasses.cardBg}`}>
                        <h3 className="text-md font-semibold mb-4 flex items-center gap-2">
                           <TrendingUp size={16}/> Sentiment Over Time
                        </h3>
                        <SentimentChart analyticsData={message.sentimentData} />
                      </div>
                    )}

                    {/* --- EVIDENCE & TOPICS LIST --- */}
                    {message.evidences &&
                      typeof message.evidences === "object" &&
                      Object.keys(message.evidences).length > 0 && (
                        <div className="mt-8 pt-4 border-t border-gray-700/50">
                          <h4 className={`font-semibold text-xs uppercase tracking-wider mb-4 flex items-center gap-2 ${themeClasses.subText}`}>
                            <Info size={14} />
                            {selectedTool === "perception"
                              ? "Trend Insights & Raw Data"
                              : "Evidence from credible sources"}
                          </h4>

                          <div className="grid gap-3">
                            {Object.entries(message.evidences).map(
                              ([date, ev], idx) => (
                                <div
                                  key={idx}
                                  className={`p-3 rounded-lg border ${themeClasses.border} ${isDarkMode ? "bg-gray-700/30" : "bg-gray-50"}`}
                                >
                                  {"average_sentiment_score" in ev ? (
                                    <>
                                      <div className="font-medium text-sm text-indigo-400">
                                        📅 {date}
                                      </div>
                                      <div className={`text-xs mt-1 ${themeClasses.subText}`}>
                                        Avg Sentiment:{" "}
                                        <span className={ev.average_sentiment_score > 0 ? "text-green-400" : "text-red-400"}>
                                           {ev.average_sentiment_score}
                                        </span>
                                      </div>
                                      
                                      {/* --- FIXED TOPICS DISPLAY --- */}
                                      <div className="text-xs mt-2 opacity-80">
                                        <span className="font-semibold text-gray-500 uppercase tracking-wide text-[10px]">Topics:</span>{" "}
                                        {Array.isArray(ev.dominant_topics) 
                                            ? ev.dominant_topics.join(", ") 
                                            : (ev.dominant_topics || "No topics detected")}
                                      </div>
                                    </>
                                  ) : (
                                    <>
                                      <div className="font-medium text-sm text-blue-400">
                                        {ev.title}
                                      </div>
                                      <div className={`text-xs mb-2 ${themeClasses.subText}`}>
                                        {ev.source} • {ev.date}
                                      </div>
                                      <p className="text-sm opacity-90">{ev.snippet}</p>
                                    </>
                                  )}
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
               <div className="flex gap-4 py-6">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center animate-pulse">
                     <Bot size={18} className="text-white" />
                  </div>
                  <div className="flex items-center">
                     <div className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 ${isDarkMode ? "text-gray-300" : "text-gray-600"}`}>
                        <Loader2 className="animate-spin" size={16} />
                        Evo is thinking...
                     </div>
                  </div>
               </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Box */}
        <div className={`border-t ${themeClasses.border} p-4`}>
          <div className="max-w-4xl mx-auto">
            <div className={`relative flex items-end gap-2 ${themeClasses.inputBg} rounded-2xl p-2 border ${themeClasses.inputBorder} shadow-sm`}>
              <select
                value={selectedTool}
                onChange={(e) => setSelectedTool(e.target.value)}
                disabled={isLoading}
                className={`text-sm px-3 py-2 rounded-xl focus:outline-none bg-transparent ${themeClasses.text} font-medium cursor-pointer hover:opacity-80`}
              >
                <option value="counterspeech" className="text-gray-900">Counterspeech Generator</option>
                <option value="perception" className="text-gray-900">Perception Trend Analysis</option>
              </select>

              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                placeholder={isLoading ? "Please wait..." : `Message Evo... (${selectedTool})`}
                className={`flex-1 bg-transparent border-none outline-none resize-none max-h-48 px-2 py-2 ${themeClasses.text} placeholder-gray-500`}
                rows="1"
                style={{ minHeight: "24px", maxHeight: "200px" }}
                onInput={(e) => {
                  e.target.style.height = "auto";
                  e.target.style.height = e.target.scrollHeight + "px";
                }}
              />

              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`p-2 rounded-lg transition-all duration-200 ${
                  input.trim() && !isLoading
                    ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md"
                    : "bg-gray-700/20 text-gray-400 cursor-not-allowed"
                }`}
              >
                {isLoading ? <Loader2 size={18} className="animate-spin"/> : <Send size={18} />}
              </button>
            </div>

            <p className={`text-xs text-center mt-2 ${themeClasses.subText}`}>
              Evo can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}