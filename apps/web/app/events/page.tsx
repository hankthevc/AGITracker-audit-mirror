"use client";

import React, { useState, useMemo } from "react";
import { EventCard, EventData } from "@/components/events/EventCard";
import { rowsToCsv } from "@/lib/csv";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Download, Filter, X } from "lucide-react";

// This will be replaced with actual API call
async function fetchEvents(): Promise<EventData[]> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/v1/events?include_analysis=true&limit=100`);
    if (!response.ok) {
      throw new Error("Failed to fetch events");
    }
    const data = await response.json();
    // API returns {total, results, items} - use items or results array
    return data.items || data.results || data || [];
  } catch (error) {
    console.error("Error fetching events:", error);
    return [];
  }
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventData[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [dateFilter, setDateFilter] = useState<string>("all");
  const [linkedOnly, setLinkedOnly] = useState(false);
  const [showRetracted, setShowRetracted] = useState(false);

  // Fetch events on mount
  React.useEffect(() => {
    fetchEvents().then(setEvents);
  }, []);

  // Filtered events
  const filteredEvents = useMemo(() => {
    return (events || []).filter((event) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          event.title.toLowerCase().includes(query) ||
          event.summary?.toLowerCase().includes(query) ||
          event.publisher.toLowerCase().includes(query);
        if (!matchesSearch) return false;
      }

      // Tier filter
      if (tierFilter !== "all" && event.evidence_tier !== tierFilter) {
        return false;
      }

      // Date filter
      if (dateFilter !== "all") {
        const eventDate = new Date(event.published_at);
        const now = new Date();
        const daysAgo = Math.floor((now.getTime() - eventDate.getTime()) / (1000 * 60 * 60 * 24));

        if (dateFilter === "7days" && daysAgo > 7) return false;
        if (dateFilter === "30days" && daysAgo > 30) return false;
        if (dateFilter === "90days" && daysAgo > 90) return false;
        if (dateFilter === "180days" && daysAgo > 180) return false;
      }

      // Linked filter
      if (linkedOnly && (!event.signpost_links || event.signpost_links.length === 0)) {
        return false;
      }

      // Retracted filter
      if (!showRetracted && event.retracted) {
        return false;
      }

      return true;
    });
  }, [events, searchQuery, tierFilter, dateFilter, linkedOnly, showRetracted]);

  // Export to JSON
  const exportJSON = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `agi-tracker-events-${new Date().toISOString().split("T")[0]}.json`;
    link.click();
  };

  // Export to CSV using centralized sanitizer (imported at top)
  const exportCSV = () => {
    const headers = ["ID", "Title", "Publisher", "Date", "Tier", "Signposts", "Significance", "URL"];
    const rows = filteredEvents.map((e) => [
      e.id,
      e.title,  // rowsToCsv handles sanitization
      e.publisher,
      e.published_at.split("T")[0],
      e.evidence_tier,
      e.signpost_links?.length || 0,
      e.analysis?.significance_score?.toFixed(2) || "N/A",
      e.source_url,
    ]);

    const csv = rowsToCsv(headers, rows);
    const dataBlob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `agi-tracker-events-${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery("");
    setTierFilter("all");
    setDateFilter("all");
    setLinkedOnly(false);
    setShowRetracted(false);
  };

  const hasActiveFilters = searchQuery || tierFilter !== "all" || dateFilter !== "all" || linkedOnly;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Event Feed</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Browse AI progress events with evidence-based significance ratings
        </p>
      </div>

      {/* Filters Bar */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-4 mb-6 space-y-4">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[250px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search events, publishers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Tier Filter */}
          <Select value={tierFilter} onValueChange={setTierFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All tiers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All tiers</SelectItem>
              <SelectItem value="A">A-tier (Peer-reviewed)</SelectItem>
              <SelectItem value="B">B-tier (Official labs)</SelectItem>
              <SelectItem value="C">C-tier (Press)</SelectItem>
              <SelectItem value="D">D-tier (Social)</SelectItem>
            </SelectContent>
          </Select>

          {/* Date Filter */}
          <Select value={dateFilter} onValueChange={setDateFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All time" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All time</SelectItem>
              <SelectItem value="7days">Last 7 days</SelectItem>
              <SelectItem value="30days">Last 30 days</SelectItem>
              <SelectItem value="90days">Last 90 days</SelectItem>
              <SelectItem value="180days">Last 180 days</SelectItem>
            </SelectContent>
          </Select>

          {/* Export Buttons */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={exportJSON}>
              <Download className="h-4 w-4 mr-2" />
              JSON
            </Button>
            <Button variant="outline" size="sm" onClick={exportCSV}>
              <Download className="h-4 w-4 mr-2" />
              CSV
            </Button>
          </div>
        </div>

        {/* Toggle Filters */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant={linkedOnly ? "default" : "outline"}
            size="sm"
            onClick={() => setLinkedOnly(!linkedOnly)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Linked to signposts only
          </Button>
          <Button
            variant={showRetracted ? "default" : "outline"}
            size="sm"
            onClick={() => setShowRetracted(!showRetracted)}
          >
            Show retracted
          </Button>

          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-2" />
              Clear filters
            </Button>
          )}
        </div>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-4 text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Showing <strong>{filteredEvents.length}</strong> of <strong>{events?.length || 0}</strong> events
          </span>
          {hasActiveFilters && (
            <Badge variant="secondary">
              Filters active
            </Badge>
          )}
        </div>
      </div>

      {/* Events List */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            {events?.length === 0 ? "No events found. Check back soon!" : "No events match your filters."}
          </p>
          {hasActiveFilters && (
            <Button variant="link" onClick={clearFilters} className="mt-2">
              Clear filters
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}

      {/* Load More (for pagination in the future) */}
      {filteredEvents.length >= 100 && (
        <div className="text-center mt-8">
          <Button variant="outline">Load more events</Button>
        </div>
      )}
    </div>
  );
}
