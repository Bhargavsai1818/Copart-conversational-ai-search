import React from 'react'

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function UserBubble({ text, time }) {
  return (
    <div className="bubble-row user">
      <div className="bubble-avatar user">You</div>
      <div>
        <div className="bubble user">{text}</div>
        <div className="bubble-time" style={{ textAlign: 'right' }}>{formatTime(time)}</div>
      </div>
    </div>
  )
}

export function BotBubble({ text, time }) {
  return (
    <div className="bubble-row bot">
      <div className="bubble-avatar bot">AI</div>
      <div>
        <div className="bubble bot">{text}</div>
        <div className="bubble-time">{formatTime(time)}</div>
      </div>
    </div>
  )
}

export function TypingBubble() {
  return (
    <div className="bubble-row bot">
      <div className="bubble-avatar bot">AI</div>
      <div className="typing-indicator">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  )
}
