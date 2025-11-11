/**
 * Loading state for Home page (Sprint 9)
 * Improves perceived performance with skeleton UI
 */
export default function HomeLoading() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Gauge skeleton */}
      <div className="mb-8 flex items-center justify-center">
        <div className="w-80 h-80 bg-gray-200 dark:bg-gray-800 rounded-full animate-pulse"></div>
      </div>

      {/* Lane progress skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white dark:bg-gray-900 border rounded-lg p-4">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-3 animate-pulse"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2 animate-pulse"></div>
            <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded w-full animate-pulse"></div>
          </div>
        ))}
      </div>

      {/* Changelog skeleton */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-6">
        <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-4 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    </div>
  );
}
