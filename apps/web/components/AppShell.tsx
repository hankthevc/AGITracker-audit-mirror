'use client'

/**
 * AppShell - Site-wide navigation and theme toggle
 * Sticky header with blur backdrop, responsive nav, theme persistence
 */

import Link from 'next/link'
import { useEffect, useState } from 'react'
import styles from './AppShell.module.css'

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
    
    // Initialize theme from localStorage or system preference
    const stored = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const theme = stored || (prefersDark ? 'dark' : 'light')
    document.documentElement.setAttribute('data-theme', theme)
  }, [])
  
  const toggleTheme = () => {
    const html = document.documentElement
    const current = html.getAttribute('data-theme')
    const next = current === 'dark' ? 'light' : 'dark'
    html.setAttribute('data-theme', next)
    localStorage.setItem('theme', next)
  }
  
  return (
    <>
      <a className="visually-hidden" href="#main">Skip to content</a>
      
      <header className={styles.header}>
        <div className="container">
          <div className={styles.row}>
            <Link href="/" className={styles.brand}>
              <span className={styles.dot} aria-hidden="true" />
              <strong>AGI Tracker</strong>
            </Link>
            
            <nav className={styles.nav} aria-label="Main navigation">
              <Link href="/signposts">Signposts</Link>
              <Link href="/simulate">Simulate</Link>
              <Link href="/forecasts">Forecasts</Link>
              <Link href="/incidents">Incidents</Link>
              <Link href="/stories">Stories</Link>
            </nav>
            
            {mounted && (
              <button
                className={styles.themeToggle}
                onClick={toggleTheme}
                aria-label="Toggle theme"
                type="button"
              >
                <span className={styles.themeIcon} aria-hidden="true">◐</span>
              </button>
            )}
          </div>
        </div>
      </header>
      
      <main id="main">{children}</main>
      
      <footer className={styles.footer}>
        <div className="container">
          <div className={styles.footerContent}>
            <span>© {new Date().getFullYear()} AGI Tracker</span>
            <span className={styles.footerDivider}>•</span>
            <Link href="/legal/privacy">Privacy</Link>
            <span className={styles.footerDivider}>•</span>
            <Link href="/legal/terms">Terms</Link>
            <span className={styles.footerDivider}>•</span>
            <Link href="/methodology">Methodology</Link>
          </div>
        </div>
      </footer>
    </>
  )
}

