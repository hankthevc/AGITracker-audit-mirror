'use client'

/**
 * Design Diagnostics - Verify design tokens are loading in production
 */

export default function Diagnostics() {
  const vars = [
    '--brand', '--bg', '--text', '--surface', 
    '--chart-1', '--chart-2', '--radius-lg', 
    '--space-4', '--step-3', '--font-sans', '--font-serif'
  ]
  
  const read = (v: string) => {
    if (typeof window === 'undefined') return '(SSR)'
    return getComputedStyle(document.documentElement).getPropertyValue(v).trim()
  }
  
  const htmlCls = typeof document === 'undefined' 
    ? 'ssr' 
    : document.documentElement.className
  
  const navItems = typeof document !== 'undefined'
    ? [...document.querySelectorAll('header nav a')].map(a => (a as HTMLAnchorElement).textContent?.trim()).join(' · ')
    : '(SSR)'
  
  return (
    <main style={{ padding: '2rem', fontFamily: 'var(--font-sans)' }}>
      <h1 style={{ fontFamily: 'var(--font-serif)' }}>Design Diagnostics</h1>
      
      <section style={{ marginTop: '2rem' }}>
        <h2>HTML Classes</h2>
        <code style={{ display: 'block', padding: '1rem', background: 'var(--surface)', borderRadius: 'var(--radius-sm)' }}>
          {htmlCls}
        </code>
      </section>
      
      <section style={{ marginTop: '2rem' }}>
        <h2>CSS Variables</h2>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {vars.map(v => (
            <li key={v} style={{ padding: '.5rem 0', borderBottom: '1px solid var(--border)' }}>
              <code style={{ color: 'var(--brand)' }}>{v}</code>
              {' = '}
              <code style={{ background: 'var(--surface)', padding: '.25rem .5rem', borderRadius: '4px' }}>
                {read(v) || '(not set)'}
              </code>
            </li>
          ))}
        </ul>
      </section>
      
      <section style={{ marginTop: '2rem' }}>
        <h2>Navigation Items</h2>
        <p><strong>Found:</strong> {navItems}</p>
        <p><strong>Expected:</strong> Simulate · Forecasts · Incidents · Stories</p>
      </section>
      
      <section style={{ marginTop: '2rem' }}>
        <h2>Theme Toggle Test</h2>
        <button
          onClick={() => {
            const html = document.documentElement
            const current = html.getAttribute('data-theme')
            const next = current === 'dark' ? 'light' : 'dark'
            html.setAttribute('data-theme', next)
          }}
          style={{
            padding: '.75rem 1.5rem',
            background: 'var(--brand)',
            color: 'white',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer'
          }}
        >
          Toggle Theme (Watch Colors Change)
        </button>
      </section>
    </main>
  )
}

