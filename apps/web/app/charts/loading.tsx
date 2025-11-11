import { Card, CardContent, CardHeader } from '@/components/ui/card'

export default function ChartsLoading() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>

      {/* Controls Skeleton */}
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-100 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Chart Skeleton */}
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
        </CardHeader>
        <CardContent>
          <div className="h-96 bg-gray-100 rounded"></div>
        </CardContent>
      </Card>
    </div>
  )
}

