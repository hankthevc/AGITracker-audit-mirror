"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Search, X, Loader2, Filter, Clock } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"

interface SearchResult {
  id: number
  title: string
  summary: string
  publisher: string
  published_at: string
  evidence_tier: "A" | "B" | "C" | "D"
}

const STORAGE_KEY = 'search-history'

export function SearchBar() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [tierFilter, setTierFilter] = useState<string>("all")
  const [showHistory, setShowHistory] = useState(false)
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Load search history from localStorage
  useEffect(() => {
    const history = localStorage.getItem(STORAGE_KEY)
    if (history) {
      setSearchHistory(JSON.parse(history))
    }
  }, [])
  
  // Save search to history - memoized to prevent recreation
  const saveToHistory = useCallback((searchQuery: string) => {
    const history = [searchQuery, ...searchHistory.filter(h => h !== searchQuery)].slice(0, 5)
    setSearchHistory(history)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history))
  }, [searchHistory])

  // Debounced search
  useEffect(() => {
    if (query.length < 2) {
      setResults([])
      setIsOpen(false)
      setShowHistory(query.length === 0 && searchHistory.length > 0)
      return
    }

    setIsLoading(true)
    setShowHistory(false)
    const timer = setTimeout(async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
        let url = `${apiUrl}/v1/search?q=${encodeURIComponent(query)}&limit=5`
        if (tierFilter !== "all") {
          url += `&tier=${tierFilter}`
        }
        
        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          setResults(data.results || [])
          setIsOpen(true)
        }
      } catch (error) {
        console.error("Search error:", error)
      } finally {
        setIsLoading(false)
      }
    }, 300) // 300ms debounce

    return () => clearTimeout(timer)
  }, [query, tierFilter, searchHistory.length])

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setShowHistory(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])
  
  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || results.length === 0) return
      
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : prev))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : 0))
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault()
        const result = results[selectedIndex]
        if (result) {
          window.location.href = `/events/${result.id}`
        }
      } else if (e.key === 'Escape') {
        setIsOpen(false)
        setShowHistory(false)
      }
    }
    
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, results, selectedIndex])
  
  // Memoized event handlers to prevent unnecessary re-renders
  const handleHistoryClick = useCallback((historyQuery: string) => {
    setQuery(historyQuery)
    setShowHistory(false)
  }, [])
  
  const handleSearch = useCallback(() => {
    if (query.length >= 2) {
      saveToHistory(query)
    }
  }, [query, saveToHistory])
  
  const handleClearSearch = useCallback(() => {
    setQuery("")
    setResults([])
    setIsOpen(false)
    setSelectedIndex(-1)
  }, [])

  const tierColors = {
    A: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    B: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
    C: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20",
    D: "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20",
  }

  return (
    <div ref={searchRef} className="relative w-full max-w-md">
      <div className="flex gap-2" role="search">
        <div className="relative flex-1">
          <Search 
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" 
            aria-hidden="true"
          />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search events, signposts..."
            className="pl-10 pr-10"
            aria-label="Search events and signposts"
            aria-autocomplete="list"
            aria-controls="search-results"
            aria-expanded={isOpen}
            aria-activedescendant={selectedIndex >= 0 ? `result-${selectedIndex}` : undefined}
            role="combobox"
            onFocus={() => {
              if (query.length >= 2) {
                setIsOpen(true)
              } else if (searchHistory.length > 0) {
                setShowHistory(true)
              }
            }}
          />
          {query && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded"
              aria-label="Clear search"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading" />
              ) : (
                <X className="h-4 w-4" aria-hidden="true" />
              )}
            </button>
          )}
        </div>
        <Select value={tierFilter} onValueChange={setTierFilter}>
          <SelectTrigger className="w-24" aria-label="Filter search results by evidence tier">
            <Filter className="h-4 w-4 mr-2" aria-hidden="true" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent aria-label="Evidence tier filter options">
            <SelectItem value="all">All Tiers</SelectItem>
            <SelectItem value="A">Tier A</SelectItem>
            <SelectItem value="B">Tier B</SelectItem>
            <SelectItem value="C">Tier C</SelectItem>
            <SelectItem value="D">Tier D</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Search History */}
      {showHistory && searchHistory.length > 0 && (
        <div 
          className="absolute top-full mt-2 w-full bg-white dark:bg-gray-900 border rounded-lg shadow-lg z-50"
          role="listbox"
          aria-label="Recent searches"
        >
          <div className="p-2 border-b flex items-center gap-2 text-xs text-gray-500">
            <Clock className="h-3 w-3" aria-hidden="true" />
            Recent searches
          </div>
          {searchHistory.map((historyQuery, idx) => (
            <button
              key={idx}
              onClick={() => handleHistoryClick(historyQuery)}
              className="w-full text-left p-3 hover:bg-gray-50 dark:hover:bg-gray-800 border-b last:border-b-0 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              role="option"
              aria-label={`Search for ${historyQuery}`}
            >
              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3 text-gray-400" aria-hidden="true" />
                <span className="text-sm">{historyQuery}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Search results dropdown */}
      {isOpen && results.length > 0 && (
        <div 
          id="search-results"
          className="absolute top-full mt-2 w-full bg-white dark:bg-gray-900 border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto"
          role="listbox"
          aria-label="Search results"
        >
          {results.map((result, idx) => (
            <Link
              key={result.id}
              id={`result-${idx}`}
              href={`/events/${result.id}`}
              onClick={() => {
                setIsOpen(false)
                saveToHistory(query)
              }}
              className={`block p-3 hover:bg-gray-50 dark:hover:bg-gray-800 border-b last:border-b-0 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 ${
                selectedIndex === idx ? 'bg-blue-50 dark:bg-blue-900/20' : ''
              }`}
              role="option"
              aria-selected={selectedIndex === idx}
            >
              <div className="flex items-start gap-2 mb-1">
                <Badge
                  variant="outline"
                  className={`${tierColors[result.evidence_tier]} text-xs`}
                  aria-label={`Evidence tier ${result.evidence_tier}`}
                >
                  {result.evidence_tier}
                </Badge>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-1">
                    {result.title}
                  </h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mt-1">
                    {result.summary}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {result.publisher} • {new Date(result.published_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </Link>
          ))}
          {results.length === 5 && (
            <Link
              href={`/events?search=${encodeURIComponent(query)}`}
              onClick={() => {
                setIsOpen(false)
                saveToHistory(query)
              }}
              className="block p-3 text-center text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              aria-label="View all search results"
            >
              See all results →
            </Link>
          )}
          <div className="p-2 text-xs text-gray-500 text-center border-t" aria-live="polite">
            Use ↑↓ to navigate • Enter to select • Esc to close
          </div>
        </div>
      )}

      {isOpen && query.length >= 2 && results.length === 0 && !isLoading && (
        <div 
          className="absolute top-full mt-2 w-full bg-white dark:bg-gray-900 border rounded-lg shadow-lg z-50 p-4 text-center text-sm text-gray-600 dark:text-gray-400"
          role="status"
          aria-live="polite"
        >
          No results found for "{query}"
        </div>
      )}
    </div>
  )
}
