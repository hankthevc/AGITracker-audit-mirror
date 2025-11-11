import type { Metadata } from 'next'
import { Inter, Source_Serif_4, JetBrains_Mono } from 'next/font/google'
import { SentryInitializer } from '@/components/SentryInitializer'
import { KeyboardShortcutsProvider } from '@/components/KeyboardShortcutsProvider'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AppShell } from '@/components/AppShell'
import './globals.css'
import '../styles/tokens.css'
import '../styles/charts.css'

const sans = Inter({ subsets: ['latin'], variable: '--font-sans', display: 'swap' })
const serif = Source_Serif_4({ subsets: ['latin'], variable: '--font-serif', weight: ['400', '600', '700'], display: 'swap' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono', display: 'swap' })

export const metadata: Metadata = {
  title: 'AGI Signpost Tracker',
  description: 'Evidence-first dashboard tracking proximity to AGI via measurable signposts',
  openGraph: {
    title: 'AGI Signpost Tracker',
    description: 'Evidence-first dashboard tracking proximity to AGI via measurable signposts',
    type: 'website',
    images: [
      {
        url: '/api/og?title=AGI%20Signpost%20Tracker&description=Evidence-first%20dashboard%20tracking%20proximity%20to%20AGI',
        width: 1200,
        height: 630,
        alt: 'AGI Signpost Tracker',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AGI Signpost Tracker',
    description: 'Evidence-first dashboard tracking proximity to AGI via measurable signposts',
    images: ['/api/og?title=AGI%20Signpost%20Tracker&description=Evidence-first%20dashboard%20tracking%20proximity%20to%20AGI'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${mono.variable}`} suppressHydrationWarning>
      <body>
        <SentryInitializer />
        <ErrorBoundary>
          <KeyboardShortcutsProvider>
            <AppShell>{children}</AppShell>
          </KeyboardShortcutsProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
