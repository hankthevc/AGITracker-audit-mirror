/**
 * Centralized API base URL resolver.
 * 
 * With Next.js rewrite proxy in production (/v1/* → Railway API),
 * we use relative URLs in production and absolute URLs in development.
 * 
 * Resolution:
 * - Production: Empty string (use relative /v1/* - proxied by Next.js)
 * - Development: http://localhost:8000 (direct to local API)
 */

export function getApiBaseUrl(): string {
  // In browser: detect if we're on dev server (localhost:3000)
  if (typeof window !== 'undefined') {
    const { hostname, port } = window.location
    
    // Development: Next.js dev server on :3000, API on :8000
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return port === '3000' ? 'http://localhost:8000' : ''
    }
    
    // Production: use relative URLs (Next.js rewrites to Railway)
    return ''
  }
  
  // SSR: check if we're in development
  const isDev = process.env.NODE_ENV === 'development'
  return isDev ? 'http://localhost:8000' : ''
}

