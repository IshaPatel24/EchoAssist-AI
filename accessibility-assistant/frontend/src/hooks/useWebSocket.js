import { useEffect, useRef, useState, useCallback } from 'react'

export default function useWebSocket(sessionId, userId, handlers = {}) {
  const wsRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  useEffect(() => {
    if (!sessionId) return

    const wsUrl = `ws://localhost:8000/ws/voice/${sessionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      // Keep-alive ping every 25s
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 25000)
      ws._ping = ping
    }

    ws.onclose = () => {
      setIsConnected(false)
      clearInterval(ws._ping)
    }

    ws.onerror = (err) => {
      setIsConnected(false)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        switch (data.type) {
          case 'thinking':
            handlersRef.current.onThinking?.()
            break
          case 'response':
            handlersRef.current.onResponse?.(data)
            break
          case 'error':
            handlersRef.current.onError?.(data.message)
            break
          default:
            break
        }
      } catch (e) {
        console.error('WS parse error:', e)
      }
    }

    return () => {
      clearInterval(ws._ping)
      ws.close()
    }
  }, [sessionId])

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      // Fallback: REST API
      fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: data.text,
          session_id: sessionId,
          user_id: data.user_id,
        }),
      })
        .then(r => r.json())
        .then(result => handlersRef.current.onResponse?.(result))
        .catch(err => handlersRef.current.onError?.(err.message))
    }
  }, [sessionId])

  return { sendMessage, isConnected }
}
