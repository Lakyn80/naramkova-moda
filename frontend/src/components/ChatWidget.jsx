// 📁 src/components/ChatWidget.jsx
import React, { useState } from "react";

export default function ChatWidget({
  apiBaseUrl = "https://aichatbotwidget-production.up.railway.app",
  title = "AI Chatbot",
  introMessage = "Dobrý den! Jak vám mohu pomoci?",
  placeholder = "Napište zprávu...",
  position = "bottom-right",
  themeColor = "#2563eb",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: "assistant", content: introMessage }]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");

    try {
      const res = await fetch(`${apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      setMessages([...newMessages, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setMessages([...newMessages, { role: "assistant", content: "❌ Chyba serveru." }]);
    }
  };

  return (
    <>
      <div
        style={{
          position: "fixed",
          [position.includes("left") ? "left" : "right"]: "1.5rem",
          [position.includes("top") ? "top" : "bottom"]: "1.5rem",
          zIndex: 9999,
        }}
      >
        {!isOpen && (
          <button
            onClick={() => setIsOpen(true)}
            style={{
              backgroundColor: themeColor,
              color: "#fff",
              padding: "0.75rem 1rem",
              borderRadius: "9999px",
              border: "none",
              boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
              cursor: "pointer",
            }}
          >
            💬
          </button>
        )}
        {isOpen && (
          <div
            style={{
              width: "300px",
              height: "400px",
              backgroundColor: "#fff",
              borderRadius: "0.75rem",
              boxShadow: "0 2px 12px rgba(0,0,0,0.2)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                backgroundColor: themeColor,
                color: "#fff",
                padding: "0.75rem",
                fontWeight: "bold",
              }}
            >
              {title}
              <button
                style={{ float: "right", background: "transparent", color: "#fff", border: "none", fontSize: "1rem" }}
                onClick={() => setIsOpen(false)}
              >
                ✖
              </button>
            </div>
            <div style={{ flex: 1, padding: "0.5rem", overflowY: "auto", fontSize: "0.9rem" }}>
              {messages.map((msg, index) => (
                <div
                  key={index}
                  style={{
                    margin: "0.25rem 0",
                    textAlign: msg.role === "user" ? "right" : "left",
                    color: msg.role === "user" ? "#333" : "#444",
                  }}
                >
                  <span
                    style={{
                      display: "inline-block",
                      backgroundColor: msg.role === "user" ? "#f0f0f0" : "#e0e7ff",
                      padding: "0.4rem 0.6rem",
                      borderRadius: "0.5rem",
                      maxWidth: "80%",
                    }}
                  >
                    {msg.content}
                  </span>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", borderTop: "1px solid #ddd" }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={placeholder}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                style={{
                  flex: 1,
                  padding: "0.5rem",
                  border: "none",
                  outline: "none",
                }}
              />
              <button
                onClick={sendMessage}
                style={{
                  backgroundColor: themeColor,
                  color: "#fff",
                  border: "none",
                  padding: "0.5rem 1rem",
                  cursor: "pointer",
                }}
              >
                ➤
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
