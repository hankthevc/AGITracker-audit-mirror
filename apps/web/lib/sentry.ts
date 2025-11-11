/**
 * Sentry initialization for Next.js web app (env-gated).
 * Only initializes if NEXT_PUBLIC_SENTRY_DSN_WEB is set.
 */

export function initSentry() {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN_WEB
  
  if (!dsn) {
    console.log('ℹ️  Sentry not configured for web (no DSN provided)')
    return
  }
  
  // Dynamically import Sentry to avoid bundle bloat when disabled
  import('@sentry/nextjs').then((Sentry) => {
    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV || 'development',
      // Low sample rate for production
      tracesSampleRate: 0.05, // 5% of transactions
      // Scrub PII
      beforeSend(event: any) {
        // Remove user IP
        if (event.user) {
          delete event.user.ip_address
        }
        // Remove sensitive headers
        if (event.request?.headers) {
          delete event.request.headers['cookie']
          delete event.request.headers['authorization']
        }
        return event
      },
      // Don't send default PII
      sendDefaultPii: false,
    })
    console.log('✓ Sentry initialized (web)')
  }).catch((err) => {
    console.warn('⚠️  Failed to initialize Sentry:', err.message)
  })
}

