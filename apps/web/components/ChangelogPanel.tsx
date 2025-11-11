'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useChangelog } from '@/hooks/useChangelog'

export function ChangelogPanel() {
  const { data, isLoading, isError } = useChangelog(5)
  
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>What Moved This Week?</CardTitle>
          <CardDescription>Recent significant changes to the index</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="text-sm text-muted-foreground">Loading recent changes...</div>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>What Moved This Week?</CardTitle>
          <CardDescription>Recent significant changes to the index</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Unable to load changelog. Check the{' '}
            <a href="/changelog" className="text-primary hover:underline">
              Changelog page
            </a>{' '}
            for updates.
          </p>
        </CardContent>
      </Card>
    )
  }
  
  const hasEntries = data.results && data.results.length > 0
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>What Moved This Week?</CardTitle>
        <CardDescription>Recent significant changes to the index</CardDescription>
      </CardHeader>
      <CardContent>
        {hasEntries ? (
          <ul className="space-y-4" data-testid="delta-list">
            {data.results.map((entry) => (
              <li key={entry.id} className="border-l-2 border-primary pl-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{entry.title}</div>
                    {entry.body && (
                      <p className="text-sm text-muted-foreground mt-1">{entry.body}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-xs">
                        {entry.type}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {new Date(entry.occurred_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            No recent changes. Check the{' '}
            <a href="/changelog" className="text-primary hover:underline">
              Changelog page
            </a>{' '}
            for all updates.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

