/**
 * SECURITY: Sanitize URLs to prevent XSS via javascript: and data: schemes
 * 
 * Validates URL scheme and returns safe fallback for dangerous URLs.
 * Protects against XSS when rendering external URLs in href attributes.
 * 
 * @param url - URL from external source (arXiv, company blogs, etc.)
 * @returns Sanitized URL or '#' if dangerous
 */
export function sanitizeUrl(url: string | null | undefined): string {
  // Handle null/undefined
  if (!url) return '#'
  
  // Trim whitespace
  const trimmed = url.trim()
  
  // Empty string
  if (!trimmed) return '#'
  
  try {
    const parsed = new URL(trimmed)
    
    // SECURITY: Only allow http: and https: schemes
    // Block: javascript:, data:, file:, etc.
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      console.warn(`Blocked dangerous URL scheme: ${parsed.protocol}`)
      return '#'
    }
    
    return trimmed
  } catch (error) {
    // Invalid URL - return safe fallback
    console.warn(`Invalid URL format: ${trimmed}`)
    return '#'
  }
}

/**
 * Check if a URL is safe without modifying it
 * Useful for validation before saving to database
 */
export function isUrlSafe(url: string): boolean {
  try {
    const parsed = new URL(url)
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

