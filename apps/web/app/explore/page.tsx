'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import Link from 'next/link'
import useSWR from 'swr'
import { apiClient } from '@/lib/api'

interface Signpost {
  id: number
  code: string
  name: string
  description: string
  category: string
  baseline_value: number
  target_value: number
  unit: string
  first_class: boolean
  why_matters?: string
  current_sota_value?: number
  current_sota_model?: string
  aschenbrenner_timeline?: string
  ai2027_timeline?: string
  measurement_source?: string
}

const CATEGORY_INFO = {
  capabilities: { label: 'Capabilities', color: 'bg-blue-500', icon: '🧠', description: 'Technical AI capabilities - reasoning, coding, science' },
  agents: { label: 'Agents', color: 'bg-purple-500', icon: '🤖', description: 'Autonomous agent reliability and deployment' },
  inputs: { label: 'Inputs', color: 'bg-green-500', icon: '⚡', description: 'Compute, data, and algorithmic efficiency' },
  security: { label: 'Security', color: 'bg-red-500', icon: '🔒', description: 'Security maturity and governance' },
  economic: { label: 'Economic', color: 'bg-yellow-500', icon: '💰', description: 'Market dynamics and economic indicators' },
  research: { label: 'Research', color: 'bg-indigo-500', icon: '🔬', description: 'Research velocity and ecosystem metrics' },
  geopolitical: { label: 'Geopolitical', color: 'bg-orange-500', icon: '🌍', description: 'International competition and policy' },
  safety_incidents: { label: 'Safety Incidents', color: 'bg-pink-500', icon: '⚠️', description: 'Concrete safety failures and near-misses' },
}

export default function ExplorePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showFirstClassOnly, setShowFirstClassOnly] = useState(false)
  
  const { data: signposts, isLoading, error } = useSWR<Signpost[]>(
    '/v1/signposts',
    () => apiClient.getSignposts()
  )
  
  const filteredSignposts = useMemo(() => {
    if (!signposts) return []
    
    return signposts.filter(sp => {
      // Category filter
      if (selectedCategory && sp.category !== selectedCategory) return false
      
      // First-class filter
      if (showFirstClassOnly && !sp.first_class) return false
      
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          sp.name.toLowerCase().includes(query) ||
          sp.description?.toLowerCase().includes(query) ||
          sp.code.toLowerCase().includes(query) ||
          sp.why_matters?.toLowerCase().includes(query)
        )
      }
      
      return true
    })
  }, [signposts, selectedCategory, showFirstClassOnly, searchQuery])
  
  const signpostsByCategory = useMemo(() => {
    if (!signposts) return {}
    
    return signposts.reduce((acc, sp) => {
      if (!acc[sp.category]) acc[sp.category] = []
      acc[sp.category].push(sp)
      return acc
    }, {} as Record<string, Signpost[]>)
  }, [signposts])
  
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1,2,3,4,5,6].map(i => (
              <div key={i} className="h-64 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }
  
  if (error || !signposts) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Signposts</CardTitle>
            <CardDescription>Failed to fetch signpost data from API</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Signpost Explorer</h1>
        <p className="text-xl text-muted-foreground mb-2">
          Comprehensive view of all {signposts.length} AGI progress indicators
        </p>
        <p className="text-sm text-muted-foreground">
          Filter by category, search by name, or browse all signposts with expert forecasts and current SOTA values
        </p>
      </div>
      
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        {Object.entries(CATEGORY_INFO).map(([key, info]) => {
          const count = signpostsByCategory[key]?.length || 0
          return (
            <button
              key={key}
              onClick={() => setSelectedCategory(selectedCategory === key ? null : key)}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedCategory === key 
                  ? 'border-primary bg-primary/5 scale-105' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">{info.icon}</div>
              <div className="text-sm font-medium">{info.label}</div>
              <div className="text-2xl font-bold">{count}</div>
            </button>
          )
        })}
      </div>
      
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Input
          type="text"
          placeholder="Search signposts (name, description, code)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1"
        />
        
        <div className="flex gap-2">
          <button
            onClick={() => setShowFirstClassOnly(!showFirstClassOnly)}
            className={`px-4 py-2 rounded-md border transition-colors ${
              showFirstClassOnly 
                ? 'bg-primary text-primary-foreground border-primary' 
                : 'border-gray-300 hover:bg-gray-50'
            }`}
          >
            First-Class Only {showFirstClassOnly && '✓'}
          </button>
          
          {selectedCategory && (
            <button
              onClick={() => setSelectedCategory(null)}
              className="px-4 py-2 rounded-md border border-gray-300 hover:bg-gray-50"
            >
              Clear Filter ✕
            </button>
          )}
        </div>
      </div>
      
      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {filteredSignposts.length} of {signposts.length} signposts
          {selectedCategory && ` in ${CATEGORY_INFO[selectedCategory as keyof typeof CATEGORY_INFO].label}`}
          {showFirstClassOnly && ' (First-Class only)'}
        </p>
        
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="text-sm text-primary hover:underline"
          >
            Clear search
          </button>
        )}
      </div>
      
      {/* Signpost Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSignposts.map((signpost) => {
          const categoryInfo = CATEGORY_INFO[signpost.category as keyof typeof CATEGORY_INFO]
          const progress = signpost.current_sota_value !== null && signpost.current_sota_value !== undefined
            ? ((signpost.current_sota_value - signpost.baseline_value) / (signpost.target_value - signpost.baseline_value)) * 100
            : 0
          
          return (
            <Link key={signpost.code} href={`/signposts/${signpost.code}`}>
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="text-2xl">{categoryInfo?.icon || '📊'}</div>
                    <div className="flex gap-2 flex-wrap">
                      <Badge variant="outline" className="text-xs">
                        {categoryInfo?.label || signpost.category}
                      </Badge>
                      {signpost.first_class && (
                        <Badge className="bg-blue-600 text-xs">
                          First-Class
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  <CardTitle className="text-lg leading-tight">{signpost.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {signpost.description || 'No description available'}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="space-y-3">
                  {/* Progress Bar */}
                  {signpost.current_sota_value !== null && (
                    <div>
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>Progress</span>
                        <span>{Math.round(progress)}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 transition-all"
                          style={{ width: `${Math.min(progress, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  {/* Current SOTA */}
                  {signpost.current_sota_model && (
                    <div className="text-xs">
                      <span className="text-muted-foreground">Current Leader:</span>{' '}
                      <span className="font-medium">{signpost.current_sota_model}</span>
                    </div>
                  )}
                  
                  {/* Why It Matters */}
                  {signpost.why_matters && (
                    <div className="text-xs bg-blue-50 border border-blue-200 rounded p-2">
                      <span className="font-semibold">💡</span> {signpost.why_matters.slice(0, 120)}
                      {signpost.why_matters.length > 120 && '...'}
                    </div>
                  )}
                  
                  {/* Expert Forecasts */}
                  <div className="flex flex-wrap gap-1 text-xs">
                    {signpost.aschenbrenner_timeline && (
                      <Badge variant="outline" className="text-xs">
                        Aschenbrenner: {new Date(signpost.aschenbrenner_timeline).getFullYear()}
                      </Badge>
                    )}
                    {signpost.ai2027_timeline && (
                      <Badge variant="outline" className="text-xs">
                        AI 2027
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>
      
      {/* Empty State */}
      {filteredSignposts.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              No signposts found matching your filters.
            </p>
            <button
              onClick={() => {
                setSearchQuery('')
                setSelectedCategory(null)
                setShowFirstClassOnly(false)
              }}
              className="mt-4 text-primary hover:underline"
            >
              Clear all filters
            </button>
          </CardContent>
        </Card>
      )}
      
      {/* Category Explainer */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>About the Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {Object.entries(CATEGORY_INFO).map(([key, info]) => (
              <div key={key} className="flex gap-3">
                <div className="text-2xl">{info.icon}</div>
                <div>
                  <div className="font-semibold">{info.label}</div>
                  <div className="text-muted-foreground">{info.description}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {signpostsByCategory[key]?.length || 0} signposts
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

