import React, { useState, useRef, useEffect } from 'react';
import { Menu, Plus, Send, User, Bot } from 'lucide-react';



export default function ChatInterface() {
  const [selectedTool, setSelectedTool] = useState("counterspeech");
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hello! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [conversations, setConversations] = useState([
    { id: 1, title: 'New conversation', active: true }
  ]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

const handleSend = async () => {
  if (!input.trim()) return;

  const userMessage = {
    id: messages.length + 1,
    role: 'user',
    content: input
  };

  setMessages(prev => [...prev, userMessage]);
  const query = input;
  setInput('');

  let endpoint = "";

  if (selectedTool === "counterspeech") {
    endpoint = "http://127.0.0.1:8000/generate-counterspeech";
  } else if (selectedTool === "perception") {
    endpoint = "http://127.0.0.1:8000/analyze-perception";
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        statement: query,
        days_back: 30,
        top_k: 3
      })
    });

    const data = await response.json();

    const aiMessage = {
      id: messages.length + 2,
      role: 'assistant',
      content: data?.result?.text || data?.result?.counterspeech || "No response generated.",
      evidences: data?.result?.evidences || []
    };

    setMessages(prev => [...prev, aiMessage]);

  } catch (err) {
    const aiMessage = {
      id: messages.length + 2,
      role: "assistant",
      content: "⚠️ Something went wrong while connecting to backend."
    };
    setMessages(prev => [...prev, aiMessage]);
  }
};




  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewChat = () => {
    const newConv = {
      id: conversations.length + 1,
      title: 'New conversation',
      active: true
    };
    setConversations(conversations.map(c => ({ ...c, active: false })).concat(newConv));
    setMessages([{ id: 1, role: 'assistant', content: 'Hello! How can I help you today?' }]);
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-gray-950 flex flex-col overflow-hidden`}>
        <div className="p-3">
          <button
            onClick={startNewChat}
            className="flex items-center gap-3 w-full p-3 rounded-lg border border-gray-700 hover:bg-gray-800 transition-colors"
          >
            <Plus size={18} />
            <span>New chat</span>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-3">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`p-3 rounded-lg mb-1 cursor-pointer hover:bg-gray-800 transition-colors ${
                conv.active ? 'bg-gray-800' : ''
              }`}
            >
              <div className="text-sm truncate">{conv.title}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-700 p-4 flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <Menu size={20} />
          </button>
          <h1 className="text-lg font-semibold">Evo the Counter speech Generator</h1>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4">
            {messages.map(message => (
              <div
                key={message.id}
                className={`flex gap-4 py-6 ${
                  message.role === 'assistant' ? 'bg-gray-800/50' : ''
                }`}
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                  {message.role === 'user' ? (
                    <User size={18} />
                  ) : (
                    <Bot size={18} />
                  )}
                </div>
                <div className="flex-1 pt-1">
                  <div className="prose prose-inverevot max-w-none">
  <p>{message.content}</p>

  {message.evidences && message.evidences.length > 0 && (
    <div className="mt-4 space-y-3">
      <h4 className="font-semibold text-sm text-gray-300">Evidence from credible sources:</h4>

      {message.evidences.map((ev) => (
        <div key={ev.index} className="p-3 rounded-lg bg-gray-700/50 border border-gray-600">
          <div className="font-medium text-sm">{ev.title}</div>
          <div className="text-xs text-gray-400">
            {ev.source} • {ev.date}
          </div>

          <p className="text-sm mt-1">{ev.snippet}</p>

          {ev.url && (
            <a
              href={ev.url}
              target="_blank"
              className="text-blue-400 text-xs underline"
            >
              Read full article →
            </a>
          )}
        </div>
      ))}
    </div>
  )}
</div>

                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
<div className="border-t border-gray-700 p-4">
  <div className="max-w-3xl mx-auto">
    <div className="relative flex items-end gap-2 bg-gray-800 rounded-2xl p-2">

      {/* TOOL SELECT DROPDOWN */}
      <select
        value={selectedTool}
        onChange={(e) => setSelectedTool(e.target.value)}
        className="bg-gray-700 text-sm px-3 py-2 rounded-xl focus:outline-none border border-gray-600"
      >
        <option value="counterspeech">Counterspeech Generator</option>
        <option value="perception">Perception Trend Analysis</option>
      </select>

      {/* TEXTBOX */}
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={`Message Evo... (${selectedTool})`}
        className="flex-1 bg-transparent border-none outline-none resize-none max-h-48 px-2 py-2"
        rows="1"
        style={{ minHeight: '24px', maxHeight: '200px' }}
        onInput={(e) => {
          e.target.style.height = 'auto';
          e.target.style.height = e.target.scrollHeight + 'px';
        }}
      />

      {/* SEND BUTTON */}
      <button
        onClick={handleSend}
        disabled={!input.trim()}
        className={`p-2 rounded-lg transition-colors ${
          input.trim()
            ? 'bg-white text-gray-900 hover:bg-gray-200'
            : 'bg-gray-700 text-gray-500 cursor-not-allowed'
        }`}
      >
        <Send size={18} />
      </button>

    </div>

    <p className="text-xs text-gray-500 text-center mt-2">
      EVO can make mistakes. Check important info.
    </p>
  </div>
</div>

      </div>
    </div>
  );
}