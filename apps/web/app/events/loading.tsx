/**
 * Loading state for Events page (Sprint 9)
 * Improves perceived performance with skeleton UI
 */
export default function EventsLoading() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header skeleton */}
      <div className="mb-6">
        <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded w-1/3 mb-2 animate-pulse"></div>
        <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-2/3 animate-pulse"></div>
      </div>

      {/* Filters skeleton */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"></div>
          ))}
        </div>
      </div>

      {/* Event cards skeleton */}
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white dark:bg-gray-900 border rounded-lg p-6">
            <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-3 animate-pulse"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-full mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-5/6 animate-pulse"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
