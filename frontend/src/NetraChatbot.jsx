import React, { useEffect, useRef, useState } from "react";

/**
 * NETRA AI Chatbot — floating chat widget powered by the backend's
 * Gemini endpoint (/api/chat). Context-aware with live system state.
 */
function NetraChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hi! I'm NETRA Assistant. Ask me about detected persons, SOS status, threat levels, or emergency guidance.",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const BACKEND_CHAT_URL = `${import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000"}/api/chat`;

  // Auto-scroll to bottom when new messages arrive.
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isTyping) return;

    const userMsg = {
      role: "user",
      text: trimmed,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch(BACKEND_CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });
      const data = await res.json();
      const botMsg = {
        role: "bot",
        text: data?.response || "Sorry, I couldn't process that. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const errMsg = {
        role: "bot",
        text: "Backend unreachable. Make sure the API server (port 8000) is running.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const chatStyles = `
    .netra-chat-toggle {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 90;
      width: 56px;
      height: 56px;
      border-radius: 999px;
      background: linear-gradient(135deg, #06b6d4, #818cf8);
      border: 1px solid rgba(34,211,238,.4);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #fff;
      box-shadow: 0 0 30px rgba(34,211,238,.3), 0 8px 24px rgba(0,0,0,.4);
      transition: transform .25s ease, box-shadow .25s ease;
    }
    .netra-chat-toggle:hover {
      transform: translateY(-3px) scale(1.05);
      box-shadow: 0 0 40px rgba(34,211,238,.5), 0 12px 32px rgba(0,0,0,.5);
    }
    .netra-chat-toggle:active { transform: scale(.95); }
    .netra-chat-panel {
      position: fixed;
      bottom: 96px;
      right: 24px;
      z-index: 89;
      width: 360px;
      max-height: 480px;
      min-height: 360px;
      border-radius: 18px;
      background: rgba(2,6,23,.95);
      border: 1px solid rgba(34,211,238,.25);
      backdrop-filter: blur(16px);
      box-shadow: 0 20px 60px rgba(0,0,0,.5), 0 0 30px rgba(34,211,238,.08);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: netraChatIn .35s cubic-bezier(.16,1,.3,1) both;
    }
    @keyframes netraChatIn {
      from { opacity: 0; transform: translateY(12px) scale(.96); }
      to { opacity: 1; transform: none; }
    }
    .netra-chat-header {
      padding: 14px 18px;
      background: rgba(8,47,73,.4);
      border-bottom: 1px solid rgba(34,211,238,.15);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .netra-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .netra-chat-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 13px;
      line-height: 1.5;
      animation: netraMsgIn .3s ease both;
    }
    @keyframes netraMsgIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: none; }
    }
    .netra-chat-msg.user {
      align-self: flex-end;
      background: linear-gradient(135deg, rgba(6,182,212,.25), rgba(129,140,248,.25));
      border: 1px solid rgba(34,211,238,.3);
      color: #e0f2fe;
    }
    .netra-chat-msg.bot {
      align-self: flex-start;
      background: rgba(15,23,42,.8);
      border: 1px solid rgba(51,65,85,.5);
      color: #e2e8f0;
    }
    .netra-chat-input-area {
      padding: 12px 14px;
      border-top: 1px solid rgba(34,211,238,.15);
      background: rgba(2,6,23,.8);
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .netra-chat-input {
      flex: 1;
      padding: 10px 14px;
      border-radius: 12px;
      background: rgba(15,23,42,.8);
      border: 1px solid rgba(51,65,85,.5);
      color: #e2e8f0;
      font-size: 13px;
      outline: none;
      transition: border-color .2s ease, box-shadow .2s ease;
    }
    .netra-chat-input:focus {
      border-color: rgba(34,211,238,.5);
      box-shadow: 0 0 0 3px rgba(34,211,238,.08);
    }
    .netra-chat-send {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      background: linear-gradient(135deg, #06b6d4, #818cf8);
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 16px;
      transition: transform .2s ease, filter .2s ease;
    }
    .netra-chat-send:hover { transform: scale(1.08); filter: brightness(1.15); }
    .netra-chat-send:disabled { opacity: .5; cursor: not-allowed; transform: none; }
    .netra-typing {
      display: flex;
      gap: 4px;
      align-items: center;
      padding: 10px 14px;
    }
    .netra-typing span {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #22d3ee;
      animation: netraTyping 1.2s ease-in-out infinite;
    }
    .netra-typing span:nth-child(2) { animation-delay: -.2s; }
    .netra-typing span:nth-child(3) { animation-delay: -.4s; }
    @keyframes netraTyping {
      0%, 60%, 100% { transform: translateY(0); opacity: .4; }
      30% { transform: translateY(-6px); opacity: 1; }
    }
    @media (max-width: 640px) {
      .netra-chat-panel {
        width: calc(100vw - 32px);
        right: 16px;
        bottom: 88px;
      }
    }
  `;

  return (
    <>
      <style>{chatStyles}</style>

      {/* Toggle Button */}
      <button
        className="netra-chat-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title={isOpen ? "Close NETRA Assistant" : "Open NETRA Assistant"}
      >
        {isOpen ? "✕" : "🤖"}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="netra-chat-panel">
          {/* Header */}
          <div className="netra-chat-header">
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #06b6d4, #818cf8)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 16,
                }}
              >
                🤖
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#67e8f9" }}>
                  NETRA Assistant
                </div>
                <div style={{ fontSize: 10, color: "#64748b", fontFamily: "monospace" }}>
                  Gemini AI • System-Aware
                </div>
              </div>
            </div>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "#10b981",
                boxShadow: "0 0 8px #10b981",
                display: "inline-block",
              }}
            />
          </div>

          {/* Messages */}
          <div className="netra-chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`netra-chat-msg ${msg.role}`}>
                {msg.text}
                <div
                  style={{
                    fontSize: 9,
                    color: msg.role === "user" ? "#7dd3fc" : "#475569",
                    marginTop: 4,
                    textAlign: msg.role === "user" ? "right" : "left",
                  }}
                >
                  {msg.time}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="netra-chat-msg bot" style={{ padding: "10px 16px" }}>
                <div className="netra-typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="netra-chat-input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about status, SOS, threats..."
              className="netra-chat-input"
              disabled={isTyping}
            />
            <button
              onClick={sendMessage}
              disabled={isTyping || !input.trim()}
              className="netra-chat-send"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default NetraChatbot;
