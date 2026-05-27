import React from 'react'
import { CheckCircle, Circle } from 'lucide-react'

export default function WorkflowGuide({ step, total }) {
  if (!step || !total) return null

  const pct = Math.round((step / total) * 100)

  return (
    <div style={styles.container} role="region" aria-label={`Workflow progress: step ${step} of ${total}`}>
      <div style={styles.header}>
        <span style={styles.label}>Guided Workflow</span>
        <span style={styles.stepBadge} aria-label={`Step ${step} of ${total}`}>
          Step {step} / {total}
        </span>
      </div>

      {/* Progress bar */}
      <div
        style={styles.progressTrack}
        role="progressbar"
        aria-valuenow={step}
        aria-valuemin={1}
        aria-valuemax={total}
        aria-label={`${pct}% complete`}
      >
        <div style={{ ...styles.progressFill, width: `${pct}%` }} />
      </div>

      {/* Step dots */}
      <div style={styles.dots} aria-hidden="true">
        {Array.from({ length: Math.min(total, 10) }).map((_, i) => {
          const stepNum = i + 1
          const done = stepNum < step
          const current = stepNum === step
          return (
            <div key={i} style={{ ...styles.dot, ...(done ? styles.dotDone : current ? styles.dotCurrent : styles.dotPending) }}>
              {done
                ? <CheckCircle size={12} />
                : <Circle size={12} />
              }
            </div>
          )
        })}
        {total > 10 && <span style={styles.moreSteps}>+{total - 10}</span>}
      </div>

      <p style={styles.hint}>
        Answer each question by voice or text. Say "skip" to skip a field.
      </p>
    </div>
  )
}

const styles = {
  container: {
    margin: '0 20px 16px',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '14px 16px',
    flexShrink: 0,
  },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: 10,
  },
  label: { fontWeight: 600, fontSize: 13, color: 'var(--accent)' },
  stepBadge: {
    background: 'rgba(108,99,255,0.15)', color: 'var(--accent)',
    borderRadius: 8, padding: '2px 8px', fontSize: 12, fontWeight: 600,
  },
  progressTrack: {
    height: 6, background: 'var(--border)', borderRadius: 3,
    overflow: 'hidden', marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, var(--accent), var(--accent2))',
    borderRadius: 3,
    transition: 'width 0.4s ease',
  },
  dots: { display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 },
  dot: { display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '50%', padding: 2 },
  dotDone: { color: 'var(--accent2)' },
  dotCurrent: { color: 'var(--accent)' },
  dotPending: { color: 'var(--text3)' },
  moreSteps: { fontSize: 11, color: 'var(--text3)', alignSelf: 'center' },
  hint: { fontSize: 11, color: 'var(--text3)', marginTop: 4 },
}
