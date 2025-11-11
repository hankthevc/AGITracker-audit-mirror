import { Card, CardContent, CardHeader } from '@/components/ui/card'

export default function DashboardLoading() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Hero Skeleton */}
      <div className="bg-gray-100 rounded-lg p-8 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-2/3 mb-4"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 rounded w-4/5"></div>
        </div>
      </div>

      {/* KPI Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>

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

