/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

// SECURITY: CSP configuration for Next.js
// NOTE: Next.js REQUIRES 'unsafe-inline' for styles (React hydration, CSS-in-JS)
// We keep styles permissive but make scripts strict (no unsafe-eval in production)
// For nonce-based CSP (strictest), use Next.js middleware (future enhancement)
const isDev = process.env.NODE_ENV !== 'production'

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' ${isDev ? "'unsafe-eval'" : ''} 'unsafe-inline' https://vercel.live;
      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
      img-src 'self' blob: data: https:;
      font-src 'self' data: https://fonts.gstatic.com;
      connect-src 'self' ${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'} https://vercel.live;
      object-src 'none';
      base-uri 'self';
      form-action 'self';
      frame-ancestors 'none';
      upgrade-insecure-requests;
    `.replace(/\s{2,}/g, ' ').trim()
  },
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload'
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'Referrer-Policy',
    value: 'origin-when-cross-origin'
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()'
  }
]

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },
  // Sprint 9: Performance optimizations
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error', 'warn'] } : false,
  },
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  // API Proxy: Eliminates CORS by making API calls same-origin
  async rewrites() {
    return [
      {
        source: '/v1/:path*',
        destination: 'https://agitracker-production-6efa.up.railway.app/v1/:path*',
      },
    ]
  },
  // ✅ FIX: Add security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ]
  },
}

module.exports = withBundleAnalyzer(nextConfig)

