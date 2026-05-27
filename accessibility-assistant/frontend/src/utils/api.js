const BASE = '/api'

export async function createSession(userId) {
  const res = await fetch(`${BASE}/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  })
  return res.json()
}

export async function getPreferences(userId) {
  const res = await fetch(`${BASE}/preferences/${userId}`)
  return res.json()
}

export async function savePreferences(userId, prefs) {
  const res = await fetch(`${BASE}/preferences/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(prefs),
  })
  return res.json()
}

export async function listDocuments(userId) {
  const res = await fetch(`${BASE}/documents/${userId}`)
  return res.json()
}

export async function listTemplates() {
  const res = await fetch(`${BASE}/templates`)
  return res.json()
}

export async function sendCommand(transcript, sessionId, userId) {
  const res = await fetch(`${BASE}/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, session_id: sessionId, user_id: userId }),
  })
  return res.json()
}
