import React, { useState, useEffect } from 'react'
import VoiceInterface from './components/VoiceInterface'
import DocumentViewer from './components/DocumentViewer'
import WorkflowGuide from './components/WorkflowGuide'
import MemoryPanel from './components/MemoryPanel'
import AccessibilityBar from './components/AccessibilityBar'
import { createSession } from './utils/api'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [userId] = useState('user_' + Math.random().toString(36).slice(2, 8))
  const [activeDoc, setActiveDoc] = useState(null)
  const [workflowState, setWorkflowState] = useState(null)
  const [messages, setMessages] = useState([])
  const [a11yPrefs, setA11yPrefs] = useState({
    fontSize: 'medium',
    contrast: 'normal',
    reduceMotion: false,
  })

  // Apply accessibility preferences to document
  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', a11yPrefs.fontSize)
    document.documentElement.setAttribute('data-contrast', a11yPrefs.contrast)
  }, [a11yPrefs])

  // Create session on mount
  useEffect(() => {
    createSession(userId).then(({ session_id }) => setSessionId(session_id))
  }, [userId])

  const addMessage = (msg) => {
    setMessages(prev => [...prev, { ...msg, id: Date.now() + Math.random() }])
  }

  const handleAgentResponse = (response) => {
    addMessage({ role: 'assistant', text: response.response_text, response })

    if (response.output_url) {
      setActiveDoc({
        url: response.output_url,
        type: response.output_type,
        label: 'Your document is ready',
      })
    }

    if (response.output_type === 'workflow') {
      setWorkflowState({
        step: response.workflow_step,
        total: response.workflow_total,
      })
    } else if (response.output_type !== 'workflow') {
      setWorkflowState(null)
    }
  }

  return (
    <div className="app-layout" style={styles.layout}>
      {/* Skip link for keyboard users */}
      <a href="#main-content" className="skip-link">Skip to main content</a>

      {/* Top accessibility bar */}
      <AccessibilityBar
        prefs={a11yPrefs}
        onPrefsChange={setA11yPrefs}
        userId={userId}
      />

      <main id="main-content" style={styles.main} role="main">
        {/* Left sidebar — history + memory */}
        <aside style={styles.sidebar} aria-label="Session history and memory">
          <MemoryPanel messages={messages} userId={userId} />
        </aside>

        {/* Center — voice interface */}
        <section style={styles.center} aria-label="Voice command interface">
          <VoiceInterface
            sessionId={sessionId}
            userId={userId}
            onUserMessage={(text) => addMessage({ role: 'user', text })}
            onAgentResponse={handleAgentResponse}
            a11yPrefs={a11yPrefs}
          />
          {workflowState && (
            <WorkflowGuide
              step={workflowState.step}
              total={workflowState.total}
            />
          )}
        </section>

        {/* Right panel — document output */}
        <section style={styles.docPanel} aria-label="Document output">
          <DocumentViewer doc={activeDoc} a11yPrefs={a11yPrefs} />
        </section>
      </main>
    </div>
  )
}

const styles = {
  layout: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    background: 'var(--bg)',
  },
  main: {
    display: 'grid',
    gridTemplateColumns: '280px 1fr 360px',
    gap: '0',
    flex: 1,
    overflow: 'hidden',
    height: 'calc(100vh - 56px)',
  },
  sidebar: {
    borderRight: '1px solid var(--border)',
    overflow: 'hidden',
  },
  center: {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  docPanel: {
    borderLeft: '1px solid var(--border)',
    overflow: 'hidden',
  },
}
