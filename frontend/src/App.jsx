import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import "./App.css";

function App() {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [history, setHistory] = useState([
    { id: "h-1", title: "Quantum Computing Frameworks", date: "Today" },
    { id: "h-2", title: "Statistical Probability Models", date: "Yesterday" },
    { id: "h-3", title: "Neural Architecture Search", date: "3 days ago" }
  ]);

  const sessionId = "user-1";
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Clean, Non-Streaming implementation to pull structured JSON data smoothly
  const generateReport = async () => {
    if (!topic.trim()) return;

    const userMessage = topic;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setTopic("");
    setLoading(true);

    // Initial temporary status state while the backend performs its web crawl/inference cycles
    setMessages((prev) => [...prev, { role: "ai", content: "Thinking..." }]);

    try {
      const res = await fetch("https://ethanhunt.onrender.com/research", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: userMessage,
          session_id: sessionId
        })
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data = await res.json();
      
      // Update the chat message placeholder with the complete response
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content = data.response;
        return updated;
      });

      // Update Exploration Sidebar history logs
      setHistory(prev => [
        { 
          id: Date.now().toString(), 
          title: userMessage.length > 28 ? userMessage.substring(0, 28) + "..." : userMessage, 
          date: "Just Now" 
        },
        ...prev
      ]);

    } catch (err) {
      console.error("Detailed Browser Error Object:", err);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content = "⚠️ Failed to fetch insights. Please try your request again.";
        return updated;
      });
    }

    setLoading(false);
  };

  const handleClearHistory = () => {
    setMessages([]);
    setTopic("");
  };

  const handleCopy = async (text, index) => {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className={`app-workspace ${sidebarOpen ? "sidebar-visible" : "sidebar-hidden"}`}>
      
      {/* SIDEBAR NAVIGATION SYSTEM */}
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <div className="brand-element">
            <span className="brand-pulse"></span>
            <h3>Workspace</h3>
          </div>
          <button className="collapse-btn" onClick={() => setSidebarOpen(false)}>✕</button>
        </div>
        
        <button className="new-research-btn" onClick={handleClearHistory}>
          <span>+</span> New Session
        </button>

        <div className="history-section">
          <label className="section-label">Recent Explorations</label>
          <div className="history-list">
            {history.map((item) => (
              <div key={item.id} className="history-item" onClick={() => setTopic(item.title)}>
                <div className="history-meta">
                  <p className="history-title">{item.title}</p>
                  <span className="history-date">{item.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="sidebar-footer">
          <a href="https://www.linkedin.com/in/yashwanth-reddy-sodanapalli-a7aa6428a/" className="contact-link">
            <span className="contact-icon">✉</span> Contact Support
          </a>
        </div>
      </aside>

      {/* MAIN CONTENT STAGE */}
      <main className="main-content">
        
        {/* UTILITY GLOBAL HEADER */}
        <header className="global-navbar">
          <div className="navbar-left">
            {!sidebarOpen && (
              <button className="expand-sidebar-btn" onClick={() => setSidebarOpen(true)}>
                ☰
              </button>
            )}
            <div className="navbar-brand-title">
              <h1>♾️EthanHunt</h1>
            </div>
          </div>

          <div className="navbar-right-status">
            {messages.length > 0 && (
              <button onClick={handleClearHistory} className="clear-btn-nav">
                Clear
              </button>
            )}
          </div>
        </header>

        {/* CONTAINER CHAT COMPONENT */}
        <div className="chat-container">
          <div className="chat-wrapper">
            <div className="chat-box">
              {messages.length === 0 && (
                <div className="empty-state">
                  <div className="pulse-icon">♾️</div>
                  <h1>EthanHunt</h1>
                  <p>Advanced neural network architecture delivering context-aware insights in real time.</p>
                </div>
              )}

              {messages.map((msg, index) => (
                <div key={index} className={`bubble-container ${msg.role}`}>
                  <div className={`bubble ${msg.role}`}>
                    {msg.role === "ai" && msg.content && (
                      <button
                        className={`copy-btn ${copiedIndex === index ? "copied" : ""}`}
                        onClick={() => handleCopy(msg.content, index)}
                      >
                        {copiedIndex === index ? "✓ Copied" : "Copy"}
                      </button>
                    )}

                    {msg.role === "ai" ? (
                      <ReactMarkdown 
                        remarkPlugins={[remarkMath]} 
                        rehypePlugins={[rehypeKatex]}
                      >
                        {msg.content 
                          ? msg.content
                              .replace(/\\\[\s*/g, "$$")
                              .replace(/\s*\\\]/g, "$$")
                              .replace(/\\\(\s*/g, "$")
                              .replace(/\s*\\\)/g, "$")
                              .replace(/\(\s*(?=P\()/g, "$") 
                              .replace(/(\d+)\s*\)/g, "$1$")
                          : "Thinking..."
                        }
                      </ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          </div>

          {/* SYSTEM CONSOLE INPUT BLOCK */}
          <div className="input-box">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) generateReport();
              }}
              placeholder="Ask anything..."
              disabled={loading}
            />

            <button onClick={generateReport} disabled={!topic.trim() || loading} className="send-btn">
              {loading ? "..." : "➤"}
            </button>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;
