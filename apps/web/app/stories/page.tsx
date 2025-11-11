'use client'

/**
 * Stories Page - Weekly AGI Progress Narratives
 * 
 * Displays auto-generated weekly summaries of AGI progress including:
 * - Index movements
 * - Top movers (rising/falling signposts)
 * - Notable incidents
 * - Forecast updates
 */

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface Story {
  id: number
  week_start: string
  week_end: string
  title: string
  body: string  // Markdown
  summary: string | null
  index_delta: number | null
  top_movers: {
    rising?: string[]
    falling?: string[]
  } | null
  created_at: string
}

export default function StoriesPage() {
  const [story, setStory] = useState<Story | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadLatestStory() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/v1/stories/latest`)
        
        if (!response.ok) {
          throw new Error('Failed to load story')
        }
        
        const data = await response.json()
        setStory(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load story')
      } finally {
        setLoading(false)
      }
    }
    
    loadLatestStory()
  }, [])

  const downloadMarkdown = () => {
    if (!story) return
    
    const blob = new Blob([story.body], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `agi-story-${story.week_start}.md`
    a.click()
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center text-muted-foreground">Loading this week's story...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="text-red-600">Error: {error}</div>
        </Card>
      </div>
    )
  }

  if (!story) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="p-6 text-center text-muted-foreground">
          No stories available yet
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold">{story.title}</h1>
            <div className="text-muted-foreground mt-2">
              {new Date(story.week_start).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}
              {' - '}
              {new Date(story.week_end).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </div>
          </div>
          <Button onClick={downloadMarkdown} variant="outline">
            📥 Download .md
          </Button>
        </div>

        {/* Summary Stats */}
        {(story.index_delta !== null || story.top_movers) && (
          <Card className="p-6">
            <div className="grid grid-cols-2 gap-6">
              {story.index_delta !== null && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Index Change</div>
                  <div className={`text-2xl font-bold ${
                    story.index_delta > 0 ? 'text-green-600' : 
                    story.index_delta < 0 ? 'text-red-600' : 
                    'text-gray-600'
                  }`}>
                    {story.index_delta > 0 ? '+' : ''}
                    {story.index_delta.toFixed(2)}%
                  </div>
                </div>
              )}
              
              {story.top_movers && (
                <div>
                  <div className="text-sm text-muted-foreground mb-2">Top Movers</div>
                  <div className="space-y-1">
                    {story.top_movers.rising && story.top_movers.rising.length > 0 && (
                      <div className="flex gap-2">
                        <span className="text-green-600">↑</span>
                        <div className="text-sm">{story.top_movers.rising.join(', ')}</div>
                      </div>
                    )}
                    {story.top_movers.falling && story.top_movers.falling.length > 0 && (
                      <div className="flex gap-2">
                        <span className="text-red-600">↓</span>
                        <div className="text-sm">{story.top_movers.falling.join(', ')}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Story Body (Markdown rendered as prose) */}
        <Card className="p-8 prose prose-gray dark:prose-invert max-w-none">
          <div
            dangerouslySetInnerHTML={{ __html: story.body.split('\n').map(line => {
              // Basic markdown to HTML (simplified for now)
              if (line.startsWith('# ')) return `<h1>${line.slice(2)}</h1>`
              if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`
              if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`
              if (line.startsWith('- ')) return `<li>${line.slice(2)}</li>`
              if (line.trim() === '') return '<br />'
              return `<p>${line}</p>`
            }).join('') }}
          />
        </Card>

        {/* Methodology */}
        <Card className="p-6 bg-gray-50 dark:bg-gray-900">
          <h3 className="text-sm font-semibold mb-2">About These Stories</h3>
          <p className="text-sm text-muted-foreground">
            Weekly narratives are auto-generated based on measurable changes in the AGI Progress Index,
            signpost movements, incidents, and expert forecast updates. All claims are linked to 
            A-tier (peer-reviewed) or B-tier (official lab) evidence.
          </p>
        </Card>
      </div>
    </div>
  )
}

