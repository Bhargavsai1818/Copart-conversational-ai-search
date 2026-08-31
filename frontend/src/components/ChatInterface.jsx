import React, { useState, useRef, useEffect, useCallback } from 'react'
import { UserBubble, BotBubble, TypingBubble } from './ConversationBubble'

// Receive exampleQuery from parent (clicked welcome card)


const SUGGESTIONS = [
  'Toyota SUVs easy to fix with no airbag damage',
  'Cars with light hail for paintless repair (PDR)',
  'Run & drive Hondas under $15k in Texas',
  'What does Enhanced Vehicle mean at Copart?',
  'Can I bid without a dealer license?',
]


const WELCOME_QUERIES = [
  'Show me Toyota RAV4s under $12,000',
  'Find run-and-drive Honda Civics in California',
  'I want a drivable Ford truck under $20k',
  'Show me Tesla Model 3s with low mileage',
  'Any flood damage BMWs in Texas?',
]

export default function ChatInterface({ onResults, onFiltersChange, exampleQuery, onExampleQueryConsumed }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [hasStarted, setHasStarted] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const textareaRef = useRef(null)

  // Fire example query when parent sets it
  useEffect(() => {
    if (exampleQuery) {
      sendMessage(exampleQuery)
      onExampleQueryConsumed?.()
    }
  }, [exampleQuery]) // eslint-disable-line


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => { scrollToBottom() }, [messages, isLoading])

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    const userMsg = { role: 'user', text: trimmed, time: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInputValue('')
    setIsLoading(true)
    setHasStarted(true)

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, session_id: sessionId }),
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()

      setSessionId(data.session_id)
      onResults(data.vehicles, data.total_matches)
      onFiltersChange(data.active_filters)

      const botMsg = { role: 'bot', text: data.assistant_message, time: new Date() }
      setMessages(prev => [...prev, botMsg])
    } catch (err) {
      const errMsg = {
        role: 'bot',
        text: `Sorry, I couldn't connect to the server. Make sure the backend is running on port 8000. (${err.message})`,
        time: new Date(),
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setIsLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isLoading, sessionId, onResults, onFiltersChange])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(inputValue)
    }
  }

  const handleTextareaChange = (e) => {
    setInputValue(e.target.value)
    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleNewSession = async () => {
    if (sessionId) {
      try {
        await fetch(`/session/${sessionId}`, { method: 'DELETE' })
      } catch {}
    }
    setSessionId(null)
    setMessages([])
    setHasStarted(false)
    onResults([], 0)
    onFiltersChange({})
  }

  return (
    <aside className="chat-panel" aria-label="Conversation">
      {/* Messages */}
      <div className="chat-messages" role="log" aria-live="polite">
        {!hasStarted && messages.length === 0 && (
          <div style={{ padding: '8px 0' }}>
            <div className="bubble-row bot">
              <div className="bubble-avatar bot">AI</div>
              <div>
                <div className="bubble bot">
                  👋 Hi! I'm CopartBot. Tell me what vehicle you're looking for — make, model, price range, condition, location, or anything else.
                </div>
                <div className="bubble-time">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === 'user'
            ? <UserBubble key={i} text={msg.text} time={msg.time} />
            : <BotBubble key={i} text={msg.text} time={msg.time} />
        )}

        {isLoading && <TypingBubble />}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion chips */}
      {!hasStarted && (
        <div style={{ padding: '0 16px' }}>
          <div className="suggestions">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                className="suggestion-chip"
                onClick={() => sendMessage(s)}
                id={`suggestion-${i}`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="chat-input-area">
        <div className="chat-input-row">
          <textarea
            ref={(el) => { inputRef.current = el; textareaRef.current = el }}
            id="chat-input"
            className="chat-input"
            placeholder="Search for vehicles... (e.g. 'Toyota SUVs under $15k in Texas')"
            value={inputValue}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            rows={1}
            aria-label="Type your vehicle search query"
          />
          <button
            id="chat-send-btn"
            className="chat-send-btn"
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        {hasStarted && (
          <div style={{ marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {['Refine by price', 'Different color', 'Only run & drive', 'Start over'].map((hint, i) => (
              <button
                key={i}
                className="suggestion-chip"
                onClick={() => setInputValue(hint === 'Start over' ? 'Start over' : hint)}
                id={`refine-hint-${i}`}
                style={{ fontSize: '0.7rem' }}
              >
                {hint}
              </button>
            ))}
            <button className="new-session-btn" onClick={handleNewSession} id="new-session-btn">
              + New search
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
