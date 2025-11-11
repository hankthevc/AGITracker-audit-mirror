"use client";

import React, { useState, useMemo, Suspense } from "react";
import dynamic from "next/dynamic";
import { EventData } from "@/components/events/EventCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar, TrendingUp, AlertCircle } from "lucide-react";

// Sprint 9: Lazy load heavy Recharts components
const TimelineChart = dynamic(() => import("./TimelineChart"), {
  loading: () => (
    <div className="bg-white dark:bg-gray-900 border rounded-lg p-6 h-[500px] flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-gray-100 mx-auto mb-4"></div>
        <p className="text-gray-500 dark:text-gray-400">Loading chart...</p>
      </div>
    </div>
  ),
  ssr: false, // Don't render on server (Recharts uses DOM APIs)
});

// Fetch events with analysis
async function fetchEvents(): Promise<EventData[]> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/v1/events?include_analysis=true&limit=200`
    );
    if (!response.ok) throw new Error("Failed to fetch");
    const data = await response.json();
    // API returns {total, results, items} - use items or results array
    return data.items || data.results || data || [];
  } catch (error) {
    console.error("Error:", error);
    return [];
  }
}

const tierColors = {
  A: "#10b981", // green
  B: "#3b82f6", // blue
  C: "#eab308", // yellow
  D: "#6b7280", // gray
};

export default function TimelinePage() {
  const [events, setEvents] = useState<EventData[]>([]);
  const [viewMode, setViewMode] = useState<"scatter" | "cumulative">("scatter");
  const [tierFilter, setTierFilter] = useState<string>("all");

  React.useEffect(() => {
    fetchEvents().then(setEvents);
  }, []);

  // Prepare timeline data
  const timelineData = useMemo(() => {
    let filtered = events;
    if (tierFilter !== "all") {
      filtered = events.filter((e) => e.evidence_tier === tierFilter);
    }

    // Sort by date
    const sorted = [...filtered].sort(
      (a, b) => new Date(a.published_at).getTime() - new Date(b.published_at).getTime()
    );

    if (viewMode === "scatter") {
      // Scatter plot: each event as a point
      return sorted.map((event) => ({
        date: new Date(event.published_at).getTime(),
        dateLabel: new Date(event.published_at).toLocaleDateString(),
        significance: event.analysis?.significance_score || 0.5,
        tier: event.evidence_tier,
        title: event.title,
        id: event.id,
      }));
    } else {
      // Cumulative events over time
      const cumulative: Array<{
        date: number;
        dateLabel: string;
        count: number;
        avgSignificance: number;
      }> = [];

      let countA = 0,
        countB = 0,
        countC = 0,
        countD = 0;
      let sumSignificance = 0;

      sorted.forEach((event, idx) => {
        const date = new Date(event.published_at);

        // Count by tier
        if (event.evidence_tier === "A") countA++;
        else if (event.evidence_tier === "B") countB++;
        else if (event.evidence_tier === "C") countC++;
        else if (event.evidence_tier === "D") countD++;

        sumSignificance += event.analysis?.significance_score || 0.5;

        cumulative.push({
          date: date.getTime(),
          dateLabel: date.toLocaleDateString(),
          count: idx + 1,
          avgSignificance: sumSignificance / (idx + 1),
        });
      });

      return cumulative;
    }
  }, [events, viewMode, tierFilter]);

  // Stats
  const stats = useMemo(() => {
    const filtered = tierFilter === "all" ? events : events.filter((e) => e.evidence_tier === tierFilter);

    const tierCounts = {
      A: filtered.filter((e) => e.evidence_tier === "A").length,
      B: filtered.filter((e) => e.evidence_tier === "B").length,
      C: filtered.filter((e) => e.evidence_tier === "C").length,
      D: filtered.filter((e) => e.evidence_tier === "D").length,
    };

    const avgSignificance =
      filtered.reduce((sum, e) => sum + (e.analysis?.significance_score || 0.5), 0) / (filtered.length || 1);

    const highSignificance = filtered.filter((e) => (e.analysis?.significance_score || 0) >= 0.8).length;

    return { tierCounts, avgSignificance, highSignificance, total: filtered.length };
  }, [events, tierFilter]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">AI Progress Timeline</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Visualize the trajectory of AI capabilities over time with evidence-based significance ratings
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Total Events</span>
          </div>
          <p className="text-2xl font-bold">{stats.total}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Avg Significance</span>
          </div>
          <p className="text-2xl font-bold">{stats.avgSignificance.toFixed(2)}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500 dark:text-gray-400">High Significance</span>
          </div>
          <p className="text-2xl font-bold">{stats.highSignificance}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">≥0.8 score</p>
        </div>
        <div className="bg-white dark:bg-gray-900 border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm text-gray-500 dark:text-gray-400">By Tier</span>
          </div>
          <div className="flex gap-2 text-xs">
            <Badge variant="outline" style={{ borderColor: tierColors.A, color: tierColors.A }}>
              A: {stats.tierCounts.A}
            </Badge>
            <Badge variant="outline" style={{ borderColor: tierColors.B, color: tierColors.B }}>
              B: {stats.tierCounts.B}
            </Badge>
            <Badge variant="outline" style={{ borderColor: tierColors.C, color: tierColors.C }}>
              C: {stats.tierCounts.C}
            </Badge>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-4 mb-6 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-4">
          <Select value={viewMode} onValueChange={(v: any) => setViewMode(v)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="scatter">Scatter Plot</SelectItem>
              <SelectItem value="cumulative">Cumulative Count</SelectItem>
            </SelectContent>
          </Select>

          <Select value={tierFilter} onValueChange={setTierFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All tiers</SelectItem>
              <SelectItem value="A">A-tier only</SelectItem>
              <SelectItem value="B">B-tier only</SelectItem>
              <SelectItem value="C">C-tier only</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <p className="text-sm text-gray-500 dark:text-gray-400">
          Showing {timelineData.length} data points
        </p>
      </div>

      {/* Chart */}
      <TimelineChart timelineData={timelineData} viewMode={viewMode} />

      {/* Legend */}
      <div className="mt-6 bg-gray-50 dark:bg-gray-900/50 border rounded-lg p-4">
        <h3 className="font-semibold text-sm mb-2">Understanding the Timeline</h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>
            <strong>Scatter Plot:</strong> Each dot represents an AI progress event. Y-axis shows significance score (0-1).
          </li>
          <li>
            <strong>Cumulative View:</strong> Shows total events over time and rolling average significance.
          </li>
          <li>
            <strong>Evidence Tiers:</strong> A (green) = peer-reviewed, B (blue) = official labs, C (yellow) = press.
          </li>
          <li>
            <strong>Significance Scores:</strong> 0.9+ = major breakthrough, 0.7-0.9 = significant, 0.5-0.7 = incremental.
          </li>
        </ul>
      </div>
    </div>
  );
}
