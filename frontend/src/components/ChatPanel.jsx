import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../api.js'

/**
 * ChatPanel — LLM-powered chat sidebar.
 *
 * Props:
 *   onHighlight(ids)  — called with list of node IDs to highlight in graph
 */
function ChatPanel({ onHighlight }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! I can help you analyze the **Order to Cash** process. Ask me anything about sales orders, deliveries, billing documents, or journal entries.',
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  // Keep last 6 messages as history for conversational memory
  const getHistory = () => messages.slice(-6).map(m => ({ role: m.role, content: m.content }))

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await sendChat(text, getHistory())

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          sql: res.sql,
          guardrail: res.guardrail_triggered,
          resultCount: res.results?.length ?? 0,
        }
      ])

      // Highlight matching nodes in graph
      if (res.highlighted_ids?.length > 0) {
        onHighlight(res.highlighted_ids)
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: '⚠️ Connection error. Is the backend running?', error: true }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const QUICK_QUERIES = [
    'Which products have highest billing count?',
    'Trace flow of billing document 91150187',
    'Find broken flows (delivered but not billed)',
    'Show all completed sales orders',
  ]

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-title">
          <span className="chat-header-section">Chat with Graph</span>
          <span className="chat-header-subtitle">Order to Cash</span>
        </div>
      </div>

      {/* Agent intro block */}
      <div className="agent-intro">
        <div className="agent-avatar">D</div>
        <div className="agent-info">
          <span className="agent-name">Dodge AI</span>
          <span className="agent-role">Graph Agent</span>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Quick query chips */}
      {messages.length <= 1 && (
        <div className="quick-queries">
          {QUICK_QUERIES.map((q, i) => (
            <button key={i} className="quick-chip" onClick={() => { setInput(q); }}>
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="chat-input-area">
        <div className="chat-status-bar">
          <span className={`status-dot ${loading ? 'thinking' : ''}`} />
          <span className="status-label">{loading ? 'Dodge AI is thinking...' : 'Dodge AI is awaiting instructions'}</span>
        </div>
        <div className="chat-input-row">
          <textarea
            className="chat-textarea"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Analyze anything"
            rows={2}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

function ChatMessage({ msg }) {
  const isUser = msg.role === 'user'

  // Convert **bold** markdown to <strong> tags
  const formatContent = (text) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="msg-avatar">D</div>
      )}
      <div className="msg-body">
        {!isUser && (
          <div className="msg-meta">
            <span className="msg-name">Dodge AI</span>
            <span className="msg-role-label">Graph Agent</span>
          </div>
        )}
        <div className={`msg-bubble ${msg.guardrail ? 'guardrail' : ''} ${msg.error ? 'error' : ''}`}>
          <p>{formatContent(msg.content)}</p>
          {msg.sql && (
            <details className="sql-detail">
              <summary>View generated SQL ({msg.resultCount} rows)</summary>
              <pre className="sql-code">{msg.sql}</pre>
            </details>
          )}
        </div>
      </div>
      {isUser && (
        <div className="msg-avatar user-avatar">Y</div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="chat-message assistant">
      <div className="msg-avatar">D</div>
      <div className="msg-body">
        <div className="msg-meta">
          <span className="msg-name">Dodge AI</span>
          <span className="msg-role-label">Graph Agent</span>
        </div>
        <div className="msg-bubble typing">
          <span /><span /><span />
        </div>
      </div>
    </div>
  )
}

export default ChatPanel
