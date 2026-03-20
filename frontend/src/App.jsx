import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your NBA Agent. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const currentInput = input;
    setInput('');
    await sendQuery(currentInput);
  };

  const handleFollowUpClick = (question) => {
    sendQuery(question);
  };

  const sendQuery = async (queryText) => {
    if (!queryText.trim() || loading) return;

    // Clear follow-ups from previous messages to keep UI clean
    setMessages(prev => prev.map(m => ({ ...m, followUps: [] })));

    const userMessage = { role: 'user', content: queryText };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post('/api/chat', { message: queryText });
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        thought: response.data.thought,
        followUps: response.data.follow_ups
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="premium-header">
        <div className="logo">
          <span className="logo-icon">🏀</span>
          <h1>NBA AI Agent</h1>
        </div>
        <div className="status-badge">Live Beta</div>
      </header>

      <main className="chat-container">
        <div className="message-list">
          {messages.map((msg, index) => (
            <div key={index} className={`message-wrapper ${msg.role}`}>
              <div className={`avatar ${msg.thought ? 'has-thought' : ''}`}>
                {msg.role === 'assistant' ? '🤖' : '👤'}
                {msg.thought && (
                  <div className="thought-tooltip">
                    <div className="thought-header">Agent Reasoning</div>
                    <div className="thought-body">{msg.thought}</div>
                  </div>
                )}
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                {msg.followUps && msg.followUps.length > 0 && (
                  <div className="follow-up-container">
                    {msg.followUps.map((q, qIndex) => (
                      <button
                        key={qIndex}
                        className="follow-up-pill"
                        onClick={() => handleFollowUpClick(q)}
                        disabled={loading}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-wrapper assistant loading">
              <div className="avatar">🤖</div>
              <div className="message-content">
                <div className="message-bubble typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="input-area" onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about NBA stats, scores, or news..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? '...' : 'Send'}
          </button>
        </form>
      </main>

      <footer className="app-footer">
        - NBA Agent by Omer Reshef - 2026
      </footer>
    </div>
  );
}

export default App;
