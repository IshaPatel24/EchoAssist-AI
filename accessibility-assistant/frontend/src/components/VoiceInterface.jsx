import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Mic, MicOff, Loader, Volume2, Send } from 'lucide-react'
import useWebSocket from '../hooks/useWebSocket'

const EXAMPLE_COMMANDS = [
  'Create a medical intake form for Jane Smith',
  'Fill out a job application',
  'Summarize my recent documents',
  'Remember I prefer large text',
  'Generate a meeting summary report',
  'Read back my last document',
]

export default function VoiceInterface({ sessionId, userId, onUserMessage, onAgentResponse, a11yPrefs }) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [textInput, setTextInput] = useState('')
  const [status, setStatus] = useState('Ready — press the mic or type a command')
  const [pulseLevel, setPulseLevel] = useState(0)

  const recognitionRef = useRef(null)
  const { sendMessage, isConnected } = useWebSocket(sessionId, userId, {
    onThinking: () => setIsProcessing(true),
    onResponse: (data) => {
      setIsProcessing(false)
      setStatus('Ready — press the mic or type a command')
      onAgentResponse(data)
    },
    onError: (err) => {
      setIsProcessing(false)
      setStatus('Error: ' + err)
    },
  })

  // Animate pulse when listening
  useEffect(() => {
    if (!isListening) { setPulseLevel(0); return }
    const iv = setInterval(() => setPulseLevel(Math.random()), 150)
    return () => clearInterval(iv)
  }, [isListening])

  // Web Speech API setup
  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setStatus('Voice not supported in this browser. Please type your command.')
      return
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = a11yPrefs?.language || 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      setStatus('Listening… speak your command')
    }
    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript
        } else {
          interim += event.results[i][0].transcript
        }
      }
      setTranscript(final || interim)
      if (final) {
        recognition.stop()
        submitTranscript(final)
      }
    }
    recognition.onerror = (e) => {
      setIsListening(false)
      setStatus('Voice error: ' + e.error + '. Try typing instead.')
    }
    recognition.onend = () => setIsListening(false)

    recognitionRef.current = recognition
    recognition.start()
  }, [a11yPrefs])

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsListening(false)
  }

  const submitTranscript = (text) => {
    if (!text.trim()) return
    setTranscript('')
    setStatus('Processing your request…')
    setIsProcessing(true)
    onUserMessage(text)
    sendMessage({ type: 'transcript', text, user_id: userId })
  }

  const submitText = () => {
    if (!textInput.trim()) return
    const text = textInput
    setTextInput('')
    submitTranscript(text)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submitText()
    }
  }

  const micSize = 80
  const pulseScale = 1 + pulseLevel * 0.3

  return (
    <div style={styles.container} role="region" aria-label="Voice command interface">
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.logo}>
          <span style={styles.logoIcon} aria-hidden="true">🎙️</span>
          <span style={styles.logoText}>VoiceForge</span>
        </div>
        <div style={styles.connStatus} aria-live="polite">
          <span style={{ ...styles.connDot, background: isConnected ? 'var(--success)' : 'var(--error)' }} />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {/* Main mic area */}
      <div style={styles.micArea}>
        {/* Pulse rings */}
        {isListening && (
          <>
            <div style={{ ...styles.pulseRing, transform: `scale(${1.4 + pulseLevel * 0.4})`, opacity: 0.15 }} aria-hidden="true" />
            <div style={{ ...styles.pulseRing, transform: `scale(${1.7 + pulseLevel * 0.3})`, opacity: 0.08 }} aria-hidden="true" />
          </>
        )}

        {/* Mic button */}
        <button
          style={{
            ...styles.micBtn,
            background: isListening
              ? 'linear-gradient(135deg, var(--accent3), #c34b7a)'
              : isProcessing
              ? 'linear-gradient(135deg, var(--accent2), #009e7e)'
              : 'linear-gradient(135deg, var(--accent), #4f46d4)',
            transform: `scale(${isListening ? pulseScale : 1})`,
          }}
          onClick={isListening ? stopListening : startListening}
          disabled={isProcessing || !isConnected}
          aria-label={isListening ? 'Stop listening' : 'Start voice command'}
          aria-pressed={isListening}
          role="button"
        >
          {isProcessing
            ? <Loader size={32} style={{ animation: 'spin 1s linear infinite' }} aria-hidden="true" />
            : isListening
            ? <MicOff size={32} aria-hidden="true" />
            : <Mic size={32} aria-hidden="true" />
          }
        </button>
      </div>

      {/* Status + live transcript */}
      <div style={styles.statusArea} aria-live="polite" aria-label="Status">
        <p style={styles.status}>{status}</p>
        {transcript && (
          <p style={styles.liveTranscript} role="status" aria-label="Live transcript">
            "{transcript}"
          </p>
        )}
      </div>

      {/* Text input fallback */}
      <div style={styles.inputArea} role="group" aria-label="Type your command">
        <label htmlFor="text-command" className="sr-only">Type a command</label>
        <textarea
          id="text-command"
          style={styles.textInput}
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Or type a command here… (Enter to send)"
          rows={2}
          aria-label="Type a command (press Enter to send)"
          disabled={isProcessing}
        />
        <button
          style={styles.sendBtn}
          onClick={submitText}
          disabled={!textInput.trim() || isProcessing}
          aria-label="Send command"
        >
          <Send size={18} aria-hidden="true" />
        </button>
      </div>

      {/* Example commands */}
      <div style={styles.examples} role="region" aria-label="Example commands">
        <p style={styles.examplesLabel}>Try saying:</p>
        <div style={styles.exampleChips}>
          {EXAMPLE_COMMANDS.map((cmd) => (
            <button
              key={cmd}
              style={styles.chip}
              onClick={() => {
                setTextInput(cmd)
                setTimeout(() => submitTranscript(cmd), 50)
              }}
              aria-label={`Example command: ${cmd}`}
            >
              {cmd}
            </button>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '24px 20px',
    height: '100%',
    overflow: 'auto',
    gap: '20px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    maxWidth: 560,
  },
  logo: { display: 'flex', alignItems: 'center', gap: 10 },
  logoIcon: { fontSize: 28 },
  logoText: { fontSize: 22, fontWeight: 700, color: 'var(--accent)', letterSpacing: '-0.5px' },
  connStatus: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text3)' },
  connDot: { width: 8, height: 8, borderRadius: '50%', display: 'inline-block' },
  micArea: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 160,
    height: 160,
  },
  pulseRing: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: '50%',
    border: '2px solid var(--accent3)',
    transition: 'transform 0.15s ease, opacity 0.15s ease',
    pointerEvents: 'none',
  },
  micBtn: {
    width: 80,
    height: 80,
    borderRadius: '50%',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    boxShadow: '0 8px 32px rgba(108,99,255,0.5)',
    transition: 'transform 0.15s ease, box-shadow 0.2s',
    zIndex: 1,
  },
  statusArea: { textAlign: 'center', maxWidth: 480 },
  status: { color: 'var(--text2)', fontSize: 14 },
  liveTranscript: {
    marginTop: 8,
    color: 'var(--accent)',
    fontStyle: 'italic',
    fontSize: 15,
    background: 'rgba(108,99,255,0.1)',
    padding: '8px 16px',
    borderRadius: 8,
  },
  inputArea: {
    display: 'flex',
    gap: 8,
    width: '100%',
    maxWidth: 560,
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    color: 'var(--text)',
    padding: '10px 14px',
    fontFamily: 'var(--font)',
    fontSize: 14,
    resize: 'none',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  sendBtn: {
    background: 'var(--accent)',
    border: 'none',
    borderRadius: 'var(--radius)',
    color: 'white',
    width: 44,
    height: 44,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  examples: { width: '100%', maxWidth: 560 },
  examplesLabel: { fontSize: 12, color: 'var(--text3)', marginBottom: 8 },
  exampleChips: { display: 'flex', flexWrap: 'wrap', gap: 6 },
  chip: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 20,
    color: 'var(--text2)',
    padding: '4px 12px',
    fontSize: 12,
    cursor: 'pointer',
    transition: 'background 0.15s, color 0.15s',
    fontFamily: 'var(--font)',
  },
}
