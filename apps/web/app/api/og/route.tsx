/**
 * OG Image Generator
 * Creates dynamic Open Graph cards for social sharing
 */

import { ImageResponse } from 'next/og'

export const runtime = 'edge'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const title = searchParams.get('title') ?? 'AGI Tracker'
  const kicker = searchParams.get('kicker') ?? 'This Week in AGI'
  
  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          height: '100%',
          background: '#0b0f19',
          color: '#f3f5f9',
          padding: 64,
          justifyContent: 'space-between'
        }}
      >
        <div
          style={{
            fontSize: 20,
            color: '#7c83ff',
            letterSpacing: 3,
            textTransform: 'uppercase',
            fontWeight: 600
          }}
        >
          {kicker}
        </div>
        
        <div
          style={{
            fontFamily: 'serif',
            fontSize: 72,
            lineHeight: 1.05,
            maxWidth: 1000,
            fontWeight: 700
          }}
        >
          {title}
        </div>
        
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 24,
            color: '#a6afc3'
          }}
        >
          <span>agi-tracker.com</span>
          <span>Data • Stories • Simulations</span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  )
}
