/**
 * Loading state for Timeline page (Sprint 9)
 * Improves perceived performance with skeleton UI
 */
export default function TimelineLoading() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header skeleton */}
      <div className="mb-8">
        <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded w-1/3 mb-2 animate-pulse"></div>
        <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-2/3 animate-pulse"></div>
      </div>

      {/* Stats cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white dark:bg-gray-900 border rounded-lg p-4">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-2 animate-pulse"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-3/4 animate-pulse"></div>
          </div>
        ))}
      </div>

      {/* Controls skeleton */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-4 mb-6">
        <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded w-1/4 animate-pulse"></div>
      </div>

      {/* Chart skeleton */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-6 h-[500px] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-gray-100 mx-auto mb-4"></div>
          <p className="text-gray-500 dark:text-gray-400">Loading timeline...</p>
        </div>
      </div>
    </div>
  );
}
