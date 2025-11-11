/**
 * URL sanitization to prevent javascript: and data: XSS attacks
 * 
 * Security: External URLs from arXiv/blogs must be validated before rendering
 * in href attributes to prevent XSS via javascript: or data: URLs.
 */

const ALLOWED_PROTOCOLS = ['http:', 'https:']

/**
 * Sanitize a URL to prevent XSS attacks via javascript: or data: URLs
 * 
 * @param url - URL from external source (arXiv, company blogs, etc.)
 * @returns Sanitized URL or '#' if invalid/dangerous
 */
export function sanitizeUrl(url: string | null | undefined): string {
  // Handle null/undefined
  if (!url) {
    return '#'
  }

  // Handle empty strings
  if (url.trim() === '') {
    return '#'
  }

  try {
    // Parse URL to check protocol
    const parsed = new URL(url)
    
    // Only allow http: and https: protocols
    if (!ALLOWED_PROTOCOLS.includes(parsed.protocol)) {
      console.warn(`Blocked dangerous URL protocol: ${parsed.protocol} in ${url}`)
      return '#'
    }
    
    // URL is safe
    return url
  } catch (error) {
    // Invalid URL format
    console.warn(`Invalid URL format: ${url}`)
    return '#'
  }
}

/**
 * Check if a URL is safe to render
 * 
 * @param url - URL to check
 * @returns true if safe, false if dangerous
 */
export function isUrlSafe(url: string | null | undefined): boolean {
  return sanitizeUrl(url) !== '#'
}

