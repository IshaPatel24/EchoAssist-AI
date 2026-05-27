import React, { useState } from 'react'
import { Settings, Eye, Type, Zap, Moon } from 'lucide-react'

export default function AccessibilityBar({ prefs, onPrefsChange, userId }) {
  const [open, setOpen] = useState(false)

  const update = (key, value) => {
    onPrefsChange(prev => ({ ...prev, [key]: value }))
  }

  return (
    <header style={styles.bar} role="banner">
      <div style={styles.left}>
        <span style={styles.brand} aria-label="VoiceForge home">
          <span aria-hidden="true">🎙️</span> VoiceForge
          <span style={styles.tagline}>Accessibility Assistant</span>
        </span>
      </div>

      <nav style={styles.quickToggles} aria-label="Quick accessibility toggles">
        {/* Font size */}
        <div style={styles.toggleGroup} role="group" aria-label="Font size">
          <Type size={14} aria-hidden="true" />
          {['medium', 'large', 'x-large'].map(size => (
            <button
              key={size}
              style={{
                ...styles.toggleBtn,
                ...(prefs.fontSize === size ? styles.toggleActive : {}),
              }}
              onClick={() => update('fontSize', size)}
              aria-pressed={prefs.fontSize === size}
              aria-label={`Font size: ${size}`}
            >
              {size === 'medium' ? 'A' : size === 'large' ? 'A+' : 'A++'}
            </button>
          ))}
        </div>

        {/* Contrast */}
        <div style={styles.toggleGroup} role="group" aria-label="Contrast mode">
          <Eye size={14} aria-hidden="true" />
          {['normal', 'high'].map(c => (
            <button
              key={c}
              style={{
                ...styles.toggleBtn,
                ...(prefs.contrast === c ? styles.toggleActive : {}),
              }}
              onClick={() => update('contrast', c)}
              aria-pressed={prefs.contrast === c}
              aria-label={`${c} contrast`}
            >
              {c === 'normal' ? 'Normal' : 'High ⚡'}
            </button>
          ))}
        </div>

        {/* Reduce motion */}
        <button
          style={{
            ...styles.toggleBtn,
            ...(prefs.reduceMotion ? styles.toggleActive : {}),
          }}
          onClick={() => update('reduceMotion', !prefs.reduceMotion)}
          aria-pressed={prefs.reduceMotion}
          aria-label="Toggle reduce motion"
          title="Reduce motion"
        >
          <Zap size={12} aria-hidden="true" />
          {prefs.reduceMotion ? 'Motion: Off' : 'Motion: On'}
        </button>
      </nav>

      <div style={styles.right}>
        <span style={styles.stack} aria-label="Powered by Omi, Qdrant, and Lyzr">
          <span style={styles.tech}>Omi</span>
          <span style={styles.techDivider}>+</span>
          <span style={styles.tech}>Qdrant</span>
          <span style={styles.techDivider}>+</span>
          <span style={styles.tech}>Lyzr</span>
        </span>
      </div>
    </header>
  )
}

const styles = {
  bar: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 20px', height: 56, background: 'var(--bg2)',
    borderBottom: '1px solid var(--border)', flexShrink: 0, gap: 16,
    flexWrap: 'wrap',
  },
  left: { display: 'flex', alignItems: 'center' },
  brand: {
    display: 'flex', alignItems: 'center', gap: 8,
    fontWeight: 700, fontSize: 15, color: 'var(--accent)',
  },
  tagline: {
    fontSize: 11, fontWeight: 400, color: 'var(--text3)',
    background: 'var(--surface)', padding: '2px 8px', borderRadius: 10,
  },
  quickToggles: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  toggleGroup: { display: 'flex', alignItems: 'center', gap: 4 },
  toggleBtn: {
    background: 'var(--surface)', border: '1px solid var(--border)',
    borderRadius: 6, color: 'var(--text2)', padding: '3px 8px',
    fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font)',
    display: 'flex', alignItems: 'center', gap: 4,
    transition: 'all 0.15s',
  },
  toggleActive: {
    background: 'rgba(108,99,255,0.2)', border: '1px solid var(--accent)',
    color: 'var(--accent)',
  },
  right: { display: 'flex', alignItems: 'center' },
  stack: { display: 'flex', alignItems: 'center', gap: 4 },
  tech: {
    background: 'var(--surface2)', border: '1px solid var(--border)',
    borderRadius: 6, padding: '2px 7px', fontSize: 11, color: 'var(--text2)',
    fontWeight: 600,
  },
  techDivider: { fontSize: 10, color: 'var(--text3)' },
}
