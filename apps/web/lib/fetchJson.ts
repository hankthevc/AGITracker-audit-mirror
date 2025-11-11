/**
 * Robust JSON fetcher with detailed error parsing.
 * 
 * Throws errors with HTTP status and response body snippet for debugging.
 */

export class FetchError extends Error {
  status: number
  statusText: string
  detail: string
  
  constructor(status: number, statusText: string, detail: string) {
    super(`HTTP ${status}: ${detail}`)
    this.name = 'FetchError'
    this.status = status
    this.statusText = statusText
    this.detail = detail
  }
}

export async function fetchJson<T = any>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      'Accept': 'application/json',
      ...init?.headers,
    },
  })
  
  if (!response.ok) {
    // Try to parse error response as JSON (FastAPI returns {detail: "..."})
    let errorDetail: string
    
    try {
      const errorJson = await response.json()
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson)
    } catch {
      // If JSON parsing fails, use response text
      try {
        errorDetail = await response.text()
      } catch {
        errorDetail = response.statusText
      }
    }
    
    // Truncate very long error messages
    if (errorDetail.length > 200) {
      errorDetail = errorDetail.substring(0, 200) + '...'
    }
    
    throw new FetchError(response.status, response.statusText, errorDetail)
  }
  
  return response.json()
}

