import { Card } from '@/components/ui/card'

export default function ExploreLoading() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>

      {/* Category Stats Skeleton */}
      <div className="grid grid-cols-4 md:grid-cols-8 gap-4 animate-pulse">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-lg"></div>
        ))}
      </div>

      {/* Signpost Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <div className="p-6 space-y-4">
              <div className="h-6 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-full"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

