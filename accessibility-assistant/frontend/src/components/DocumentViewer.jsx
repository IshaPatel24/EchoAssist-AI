import React, { useState } from 'react'
import { FileText, Download, Volume2, ExternalLink } from 'lucide-react'

export default function DocumentViewer({ doc, a11yPrefs }) {
  const [audioPlaying, setAudioPlaying] = useState(false)
  const audioRef = React.useRef(null)

  const playAudio = () => {
    if (!doc?.audioUrl) return
    if (audioPlaying) {
      audioRef.current?.pause()
      setAudioPlaying(false)
    } else {
      audioRef.current?.play()
      setAudioPlaying(true)
    }
  }

  if (!doc) {
    return (
      <div style={styles.empty} role="region" aria-label="Document output — empty">
        <div style={styles.emptyIcon} aria-hidden="true">📄</div>
        <p style={styles.emptyTitle}>No document yet</p>
        <p style={styles.emptyText}>
          Use a voice command to generate a document. Try saying "Create a medical intake form" or "Fill out a job application."
        </p>
        <div style={styles.templates} role="list" aria-label="Available templates">
          {TEMPLATE_PREVIEWS.map(t => (
            <div key={t.name} style={styles.templateCard} role="listitem">
              <span style={styles.templateIcon} aria-hidden="true">{t.icon}</span>
              <div>
                <p style={styles.templateName}>{t.name}</p>
                <p style={styles.templateDesc}>{t.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const fullUrl = doc.url.startsWith('http') ? doc.url : `http://localhost:8000${doc.url}`

  return (
    <div style={styles.container} role="region" aria-label="Generated document">
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <FileText size={20} color="var(--accent)" aria-hidden="true" />
          <span style={styles.headerTitle}>Document Ready</span>
        </div>
        <div style={styles.headerActions}>
          {doc.audioUrl && (
            <button
              style={styles.actionBtn}
              onClick={playAudio}
              aria-label={audioPlaying ? 'Pause audio' : 'Play document audio'}
              aria-pressed={audioPlaying}
            >
              <Volume2 size={16} aria-hidden="true" />
            </button>
          )}
          <a
            href={fullUrl}
            download
            style={styles.downloadBtn}
            aria-label="Download document"
          >
            <Download size={16} aria-hidden="true" />
            Download
          </a>
        </div>
      </div>

      {/* Success badge */}
      <div style={styles.successBadge} role="status" aria-live="polite">
        <span style={styles.successDot} aria-hidden="true" />
        {doc.label || 'Document generated successfully'}
      </div>

      {/* PDF preview */}
      <div style={styles.previewArea} aria-label="Document preview">
        {doc.url.endsWith('.pdf') ? (
          <iframe
            src={fullUrl}
            style={styles.pdfFrame}
            title="Generated document preview"
            aria-label="PDF document preview"
          />
        ) : (
          <div style={styles.textPreview}>
            <p style={{ color: 'var(--text2)', fontSize: 13 }}>
              Preview not available for this file type.
            </p>
            <a
              href={fullUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.openLink}
              aria-label="Open document in new tab"
            >
              Open document <ExternalLink size={14} aria-hidden="true" />
            </a>
          </div>
        )}
      </div>

      {doc.audioUrl && (
        <audio
          ref={audioRef}
          src={`http://localhost:8000${doc.audioUrl}`}
          onEnded={() => setAudioPlaying(false)}
          aria-hidden="true"
        />
      )}
    </div>
  )
}

const TEMPLATE_PREVIEWS = [
  { icon: '🏥', name: 'Medical Intake', desc: 'Patient forms & health records' },
  { icon: '💼', name: 'Job Application', desc: 'Employment applications' },
  { icon: '⚠️', name: 'Incident Report', desc: 'Document accidents & incidents' },
  { icon: '📋', name: 'Meeting Summary', desc: 'Notes & action items' },
  { icon: '♿', name: 'Accommodation Request', desc: 'Disability accommodations' },
]

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: '1px solid var(--border)',
    flexShrink: 0,
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 8 },
  headerTitle: { fontWeight: 600, fontSize: 14 },
  headerActions: { display: 'flex', gap: 8, alignItems: 'center' },
  actionBtn: {
    background: 'var(--surface2)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
    padding: '6px 10px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
  },
  downloadBtn: {
    background: 'var(--accent)',
    border: 'none',
    borderRadius: 8,
    color: 'white',
    padding: '6px 14px',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontFamily: 'var(--font)',
  },
  successBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 20px',
    background: 'rgba(0,212,170,0.1)',
    fontSize: 13,
    color: 'var(--success)',
    borderBottom: '1px solid var(--border)',
    flexShrink: 0,
  },
  successDot: {
    width: 8, height: 8, borderRadius: '50%',
    background: 'var(--success)', display: 'inline-block',
  },
  previewArea: { flex: 1, overflow: 'hidden' },
  pdfFrame: { width: '100%', height: '100%', border: 'none', background: 'white' },
  textPreview: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', height: '100%', gap: 12,
  },
  openLink: {
    display: 'flex', alignItems: 'center', gap: 4,
    color: 'var(--accent)', fontSize: 14, textDecoration: 'none',
  },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'flex-start', padding: '24px 20px', height: '100%',
    overflow: 'auto', gap: 12,
  },
  emptyIcon: { fontSize: 40, marginTop: 16 },
  emptyTitle: { fontWeight: 600, fontSize: 16 },
  emptyText: {
    color: 'var(--text2)', fontSize: 13, textAlign: 'center',
    maxWidth: 280, lineHeight: 1.6,
  },
  templates: { width: '100%', display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 },
  templateCard: {
    display: 'flex', alignItems: 'center', gap: 12,
    background: 'var(--surface)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)', padding: '10px 14px',
  },
  templateIcon: { fontSize: 22 },
  templateName: { fontWeight: 600, fontSize: 13 },
  templateDesc: { color: 'var(--text3)', fontSize: 12 },
}
