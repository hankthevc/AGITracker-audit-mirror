'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function ChartsError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Charts Error</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            Failed to load chart data. Please try again.
          </p>
          <div className="flex gap-3">
            <Button onClick={reset}>Reload Chart</Button>
            <Button variant="outline" asChild>
              <a href="/dashboard">Go to Dashboard</a>
            </Button>
          </div>
          {error.digest && (
            <p className="text-xs text-muted-foreground">Error ID: {error.digest}</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

