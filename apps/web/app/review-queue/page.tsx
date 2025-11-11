"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CheckCircle2, XCircle, Clock, TrendingUp, AlertTriangle, ExternalLink } from "lucide-react";

interface ReviewMapping {
  id: number;
  event_id: number;
  event_title: string;
  event_summary: string;
  event_tier: "A" | "B" | "C" | "D";
  signpost_id: string;
  signpost_code: string;
  signpost_name: string;
  confidence: number;
  rationale: string;
  impact_estimate: number;
  link_type: "supports" | "contradicts" | "related";
  needs_review: boolean;
  reviewed_at: string | null;
  review_status: string | null;
  created_at: string;
}

interface ReviewStats {
  total_mappings: number;
  needs_review: number;
  approved: number;
  rejected: number;
  pending_review: number;
  confidence_distribution: {
    low: number;
    medium: number;
    high: number;
  };
  review_rate: number;
}

async function fetchReviewQueue(confidence_filter: string): Promise<ReviewMapping[]> {
  const params = new URLSearchParams({
    needs_review_only: "true",
    limit: "50"
  });

  if (confidence_filter !== "all") {
    if (confidence_filter === "low") {
      params.append("max_confidence", "0.5");
    } else if (confidence_filter === "medium") {
      params.append("min_confidence", "0.5");
      params.append("max_confidence", "0.7");
    } else if (confidence_filter === "high") {
      params.append("min_confidence", "0.7");
    }
  }

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/v1/review-queue/mappings?${params}`
  );
  if (!response.ok) throw new Error("Failed to fetch");
  const data = await response.json();
  return data.mappings;
}

async function fetchStats(): Promise<ReviewStats> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/v1/review-queue/stats`
  );
  if (!response.ok) throw new Error("Failed to fetch");
  return await response.json();
}

async function approveMapping(mapping_id: number, api_key: string): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/v1/review-queue/mappings/${mapping_id}/approve`,
    {
      method: "POST",
      headers: { "x-api-key": api_key }
    }
  );
  if (!response.ok) throw new Error("Failed to approve");
}

async function rejectMapping(mapping_id: number, reason: string, api_key: string): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/v1/review-queue/mappings/${mapping_id}/reject?reason=${encodeURIComponent(reason)}`,
    {
      method: "POST",
      headers: { "x-api-key": api_key }
    }
  );
  if (!response.ok) throw new Error("Failed to reject");
}

const linkTypeColors = {
  supports: "text-green-600 dark:text-green-400",
  contradicts: "text-red-600 dark:text-red-400",
  related: "text-blue-600 dark:text-blue-400"
};

export default function ReviewQueuePage() {
  const [mappings, setMappings] = useState<ReviewMapping[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  React.useEffect(() => {
    loadData();
  }, [confidenceFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [queueData, statsData] = await Promise.all([
        fetchReviewQueue(confidenceFilter),
        fetchStats()
      ]);
      setMappings(queueData);
      setStats(statsData);
    } catch (error) {
      console.error("Error loading review queue:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (mapping_id: number) => {
    if (!apiKey) {
      alert("Please enter your API key first");
      return;
    }

    setActionLoading(mapping_id);
    try {
      await approveMapping(mapping_id, apiKey);
      await loadData(); // Refresh
    } catch (error) {
      console.error("Error approving:", error);
      alert("Failed to approve mapping");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (mapping_id: number) => {
    if (!apiKey) {
      alert("Please enter your API key first");
      return;
    }

    const reason = prompt("Reason for rejection (optional):");
    
    setActionLoading(mapping_id);
    try {
      await rejectMapping(mapping_id, reason || "Low confidence", apiKey);
      await loadData(); // Refresh
    } catch (error) {
      console.error("Error rejecting:", error);
      alert("Failed to reject mapping");
    } finally {
      setActionLoading(null);
    }
  };

  const getConfidenceBadge = (conf: number) => {
    if (conf >= 0.7) return { label: "High", color: "bg-green-500/10 text-green-700 border-green-500/20" };
    if (conf >= 0.5) return { label: "Med", color: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20" };
    return { label: "Low", color: "bg-red-500/10 text-red-700 border-red-500/20" };
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Review Queue</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Calibrate AI-generated event-signpost mappings to improve accuracy
        </p>
      </div>

      {/* API Key Input */}
      {!apiKey && (
        <Card className="mb-6 border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              <div className="flex-1">
                <p className="font-semibold mb-2">API Key Required</p>
                <input
                  type="password"
                  placeholder="Enter your API key to approve/reject mappings"
                  className="w-full px-3 py-2 border rounded-md"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Needs Review</CardDescription>
              <CardTitle className="text-3xl">{stats.needs_review}</CardTitle>
            </CardHeader>
            <CardContent>
              <Progress value={(stats.needs_review / stats.total_mappings) * 100} className="h-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Review Rate</CardDescription>
              <CardTitle className="text-3xl">{stats.review_rate}%</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>{stats.approved} approved</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Confidence Dist.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>High:</span>
                  <Badge variant="outline">{stats.confidence_distribution.high}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Med:</span>
                  <Badge variant="outline">{stats.confidence_distribution.medium}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Low:</span>
                  <Badge variant="outline">{stats.confidence_distribution.low}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Mappings</CardDescription>
              <CardTitle className="text-3xl">{stats.total_mappings}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-gray-600">
                <span>{stats.rejected} rejected</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-4 mb-6 flex justify-between items-center">
        <div className="flex gap-4">
          <Select value={confidenceFilter} onValueChange={setConfidenceFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Confidence</SelectItem>
              <SelectItem value="low">Low (&lt;0.5)</SelectItem>
              <SelectItem value="medium">Medium (0.5-0.7)</SelectItem>
              <SelectItem value="high">High (≥0.7)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <p className="text-sm text-gray-500">
          {mappings.length} mappings to review
        </p>
      </div>

      {/* Mappings List */}
      {loading ? (
        <div className="text-center py-12">
          <Clock className="h-12 w-12 mx-auto text-gray-400 animate-spin mb-4" />
          <p className="text-gray-500">Loading review queue...</p>
        </div>
      ) : mappings.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <CheckCircle2 className="h-16 w-16 mx-auto text-green-500 mb-4" />
            <p className="text-lg font-semibold mb-2">All caught up!</p>
            <p className="text-gray-500">No mappings need review right now.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {mappings.map((mapping) => (
            <Card key={mapping.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex gap-2 mb-2">
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                        {mapping.event_tier}-tier
                      </Badge>
                      <Badge variant="outline" className={getConfidenceBadge(mapping.confidence).color}>
                        {getConfidenceBadge(mapping.confidence).label}: {mapping.confidence.toFixed(2)}
                      </Badge>
                      <Badge variant="outline" className={linkTypeColors[mapping.link_type]}>
                        {mapping.link_type}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg mb-1">{mapping.event_title}</CardTitle>
                    <CardDescription>
                      Mapped to: <strong>{mapping.signpost_name}</strong> ({mapping.signpost_code})
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {/* Event Summary */}
                {mapping.event_summary && (
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                    {mapping.event_summary}
                  </p>
                )}

                {/* Mapping Rationale */}
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg mb-4">
                  <h4 className="font-semibold text-sm mb-2">AI Rationale:</h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{mapping.rationale}</p>
                  {mapping.impact_estimate !== null && (
                    <div className="mt-2 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-gray-500" />
                      <span className="text-xs text-gray-600">
                        Impact estimate: {(mapping.impact_estimate * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleApprove(mapping.id)}
                    disabled={!apiKey || actionLoading === mapping.id}
                    className="flex-1"
                    variant="default"
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    {actionLoading === mapping.id ? "Processing..." : "Approve"}
                  </Button>
                  <Button
                    onClick={() => handleReject(mapping.id)}
                    disabled={!apiKey || actionLoading === mapping.id}
                    className="flex-1"
                    variant="destructive"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    {actionLoading === mapping.id ? "Processing..." : "Reject"}
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => window.open(`/events?id=${mapping.event_id}`, "_blank")}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

