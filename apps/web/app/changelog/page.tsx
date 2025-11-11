import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function ChangelogPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Changelog</h1>
        <p className="text-xl text-muted-foreground">
          Track significant changes to the AGI proximity index
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>This page will show recent index updates and evidence additions</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            The changelog will display:
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground mt-2 space-y-1">
            <li>Significant index movements (&gt;2% change)</li>
            <li>New evidence additions (claims from A/B tier sources)</li>
            <li>Retractions and corrections</li>
            <li>Signpost threshold crossings</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

