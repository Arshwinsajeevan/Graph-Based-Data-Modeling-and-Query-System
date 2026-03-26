const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Fetch graph data (nodes + links) from the backend.
 */
export async function fetchGraph() {
  const res = await fetch(`${API_BASE}/graph`)
  if (!res.ok) throw new Error('Failed to fetch graph data')
  return res.json()
}

/**
 * Send a chat message to the LLM pipeline.
 * @param {string} message - User question
 * @param {Array}  history - [{role, content}, ...] for conversational memory
 */
export async function sendChat(message, history = []) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })
  if (!res.ok) throw new Error('Chat request failed')
  return res.json()
}
