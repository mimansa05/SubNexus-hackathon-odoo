const BASE = '/api/v1'
const TOKEN_KEY = 'subnexus.token'

export const getToken = () => {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export const setToken = (t: string | null) => {
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ }
}

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message) }
}

/** FastAPI returns `detail` as a string, or a list of validation errors. */
const messageOf = (body: unknown, fallback: string) => {
  const d = (body as { detail?: unknown } | null)?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((e) => String(e?.msg ?? '').replace(/^Value error, /, '')).join('. ')
  return fallback
}

export async function api<T>(path: string, init: { method?: string; body?: unknown; auth?: boolean } = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (init.body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getToken()
  if (init.auth !== false && token) headers.Authorization = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(BASE + path, {
      method: init.method ?? (init.body !== undefined ? 'POST' : 'GET'),
      headers,
      body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    })
  } catch {
    throw new ApiError('Cannot reach the server. Is the backend running on port 8000?', 0)
  }

  const body = await res.json().catch(() => null)
  // The dev proxy answers 5xx with a non-JSON body when the backend is down
  if (!res.ok && body === null && res.status >= 500) {
    throw new ApiError('The server did not respond properly. Check that the backend is running on port 8000 and can connect to the database (see the backend terminal).', res.status)
  }
  if (!res.ok) throw new ApiError(messageOf(body, `Request failed (${res.status})`), res.status)
  return body as T
}
