import React, { useRef, useEffect } from 'react'
import { MessageSquare, FileText, Brain } from 'lucide-react'

export default function MemoryPanel({ messages, userId }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div style={styles.container} role="region" aria-label="Conversation history">
      <div style={styles.header}>
        <Brain size={16} color="var(--accent)" aria-hidden="true" />
        <span style={styles.headerText}>Session Memory</span>
        <span style={styles.badge} aria-label={`${messages.length} messages`}>
          {messages.length}
        </span>
      </div>

      <div style={styles.messageList} role="log" aria-live="polite" aria-label="Messages">
        {messages.length === 0 ? (
          <div style={styles.empty}>
            <MessageSquare size={24} color="var(--text3)" aria-hidden="true" />
            <p style={styles.emptyText}>Your conversation history will appear here</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                ...styles.message,
                ...(msg.role === 'user' ? styles.userMsg : styles.assistantMsg),
              }}
              role="article"
              aria-label={`${msg.role === 'user' ? 'You' : 'VoiceForge'}: ${msg.text}`}
            >
              <div style={styles.msgHeader}>
                <span style={styles.roleBadge}>
                  {msg.role === 'user' ? '🎙 You' : '🤖 VoiceForge'}
                </span>
                {msg.response?.output_type && msg.response.output_type !== 'none' && (
                  <span style={styles.outputBadge} aria-label={`Output type: ${msg.response.output_type}`}>
                    <FileText size={10} aria-hidden="true" />
                    {msg.response.output_type}
                  </span>
                )}
              </div>
              <p style={styles.msgText}>{msg.text}</p>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div style={styles.footer} aria-label="User info">
        <span style={styles.userId}>Session: {userId}</span>
        <span style={styles.qdrantBadge} title="Powered by Qdrant vector memory">
          ⚡ Qdrant memory
        </span>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden',
  },
  header: {
    display: 'flex', alignItems: 'center', gap: 8, padding: '16px',
    borderBottom: '1px solid var(--border)', flexShrink: 0,
  },
  headerText: { fontWeight: 600, fontSize: 13, flex: 1 },
  badge: {
    background: 'var(--accent)', color: 'white', borderRadius: 10,
    padding: '1px 7px', fontSize: 11, fontWeight: 600,
  },
  messageList: {
    flex: 1, overflow: 'auto', padding: '12px',
    display: 'flex', flexDirection: 'column', gap: 8,
  },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    gap: 10, paddingTop: 32, opacity: 0.5,
  },
  emptyText: { fontSize: 12, color: 'var(--text3)', textAlign: 'center' },
  message: {
    borderRadius: 'var(--radius-sm)', padding: '10px 12px',
    border: '1px solid var(--border)',
  },
  userMsg: { background: 'rgba(108,99,255,0.08)' },
  assistantMsg: { background: 'var(--surface)' },
  msgHeader: { display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 },
  roleBadge: { fontSize: 11, fontWeight: 600, color: 'var(--text2)' },
  outputBadge: {
    display: 'flex', alignItems: 'center', gap: 3,
    background: 'rgba(0,212,170,0.15)', color: 'var(--accent2)',
    borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 600,
  },
  msgText: { fontSize: 12, color: 'var(--text)', lineHeight: 1.5, wordBreak: 'break-word' },
  footer: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '10px 14px', borderTop: '1px solid var(--border)',
    flexShrink: 0,
  },
  userId: { fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)' },
  qdrantBadge: { fontSize: 10, color: 'var(--accent2)', cursor: 'help' },
}
