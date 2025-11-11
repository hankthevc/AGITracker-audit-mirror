'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'

export function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <nav className="border-b bg-white/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="text-2xl font-bold text-primary whitespace-nowrap">
            AGI Signpost Tracker
          </Link>
          
          {/* Desktop Search Bar */}
          <div className="hidden md:block flex-1 max-w-md mx-4">
            <SearchBar />
          </div>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex gap-4 flex-wrap">
            <Link href="/" className="text-sm font-medium hover:text-primary transition-colors">
              Home
            </Link>
            <Link href="/dashboard" className="text-sm font-medium hover:text-primary transition-colors">
              📊 Dashboard
            </Link>
            <Link href="/explore" className="text-sm font-medium hover:text-primary transition-colors">
              🔭 Explore
            </Link>
            <Link href="/charts" className="text-sm font-medium hover:text-primary transition-colors">
              📈 Charts
            </Link>
            <Link href="/insights" className="text-sm font-medium hover:text-primary transition-colors">
              🔍 Insights
            </Link>
            <Link href="/news" className="text-sm font-medium hover:text-primary transition-colors">
              News
            </Link>
            <Link href="/events" className="text-sm font-medium hover:text-primary transition-colors">
              Events
            </Link>
            <Link href="/benchmarks" className="text-sm font-medium hover:text-primary transition-colors">
              Benchmarks
            </Link>
            <Link href="/compute" className="text-sm font-medium hover:text-primary transition-colors">
              Compute
            </Link>
            <Link href="/security" className="text-sm font-medium hover:text-primary transition-colors">
              Security
            </Link>
            <Link href="/changelog" className="text-sm font-medium hover:text-primary transition-colors">
              Changelog
            </Link>
            <Link href="/methodology" className="text-sm font-medium hover:text-primary transition-colors">
              Methodology
            </Link>
            <Link href="/admin/review" className="text-sm font-medium hover:text-primary transition-colors">
              Admin
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden mt-4 pb-4 space-y-2">
            {/* Mobile Search */}
            <div className="mb-4">
              <SearchBar />
            </div>
            
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Home
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              📊 Dashboard
            </Link>
            <Link
              href="/explore"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              🔭 Explore All Signposts
            </Link>
            <Link
              href="/charts"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              📈 Charts
            </Link>
            <Link
              href="/insights"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              🔍 Insights
            </Link>
            <Link
              href="/news"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              News
            </Link>
            <Link
              href="/events"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Events
            </Link>
            <Link
              href="/benchmarks"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Benchmarks
            </Link>
            <Link
              href="/compute"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Compute
            </Link>
            <Link
              href="/security"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Security
            </Link>
            <Link
              href="/changelog"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Changelog
            </Link>
            <Link
              href="/methodology"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Methodology
            </Link>
            <Link
              href="/admin/review"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
            >
              Admin
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
