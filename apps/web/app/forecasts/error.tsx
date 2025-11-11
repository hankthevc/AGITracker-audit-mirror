'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Forecasts error:', error)
  }, [error])

  return (
    <div className="container mx-auto px-4 py-16 max-w-2xl text-center">
      <h2 className="text-2xl font-bold mb-4">Failed to Load Forecasts</h2>
      <p className="text-muted-foreground mb-6">
        Unable to load expert timeline predictions. This might be a temporary issue.
      </p>
      <div className="flex gap-4 justify-center">
        <Button onClick={() => reset()}>Try Again</Button>
        <Button variant="outline" onClick={() => window.location.href = '/'}>
          Return Home
        </Button>
      </div>
    </div>
  )
}

