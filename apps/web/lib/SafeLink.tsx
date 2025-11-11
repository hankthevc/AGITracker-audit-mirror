/**
 * SafeLink - Secure link component that prevents XSS via javascript: and data: URLs
 * 
 * SECURITY: Always use this component instead of raw <a> tags when rendering
 * URLs from external sources (arXiv, company blogs, user input, LLM output, etc.)
 * 
 * Blocks dangerous URL schemes and enforces noopener/noreferrer.
 */

import React from 'react'

const ALLOWED_PROTOCOLS = ['http:', 'https:', 'mailto:']

export interface SafeLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href?: string
  children: React.ReactNode
}

export function SafeLink({ href, children, className, ...rest }: SafeLinkProps) {
  // Handle missing href
  if (!href) {
    return <span className={className}>{children}</span>
  }

  // Validate URL scheme
  try {
    // Parse URL (use placeholder base for relative URLs)
    const parsed = new URL(href, 'http://placeholder.local')
    
    // Check if protocol is allowed
    if (!ALLOWED_PROTOCOLS.includes(parsed.protocol)) {
      console.warn(`[SafeLink] Blocked dangerous URL scheme: ${parsed.protocol} in ${href}`)
      // Render as plain text instead of clickable link
      return <span className={className} title={`Blocked unsafe URL: ${href}`}>{children}</span>
    }
  } catch (error) {
    // Invalid URL - render as plain text
    console.warn(`[SafeLink] Invalid URL format: ${href}`)
    return <span className={className}>{children}</span>
  }

  // Safe URL - render as link with security attributes
  return (
    // eslint-disable-next-line no-restricted-syntax
    <a
      href={href}
      rel="noopener noreferrer"  // Prevent window.opener access and referrer leakage
      className={className}
      {...rest}
    >
      {children}
    </a>
  )
}

/**
 * Hook version for programmatic URL validation
 */
export function useSafeUrl(url: string | null | undefined): string | null {
  if (!url) return null

  try {
    const parsed = new URL(url, 'http://placeholder.local')
    if (ALLOWED_PROTOCOLS.includes(parsed.protocol)) {
      return url
    }
    return null
  } catch {
    return null
  }
}

