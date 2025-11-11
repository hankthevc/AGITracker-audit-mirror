"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink, AlertTriangle, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RetractionBanner } from "@/components/events/RetractionBanner";
import { SafeLink } from "@/lib/SafeLink";

export interface EventAnalysis {
  summary: string;
  relevance_explanation?: string;
  significance_score: number;
  impact_json?: {
    capabilities?: string;
    timelines?: string;
    safety_implications?: string;
  };
}

export interface EventData {
  id: number;
  title: string;
  summary: string;
  source_url: string;
  publisher: string;
  published_at: string;
  evidence_tier: "A" | "B" | "C" | "D";
  provisional: boolean;
  needs_review: boolean;
  retracted: boolean;
  retracted_at?: string;
  retraction_reason?: string;
  retraction_evidence_url?: string;
  // Sprint 10: URL validation fields
  url_is_valid?: boolean;
  url_status_code?: number;
  url_error?: string;
  url_validated_at?: string;
  signpost_links?: Array<{
    signpost_id: string;
    signpost_name: string;
    link_type: "supports" | "contradicts" | "related";
  }>;
  analysis?: EventAnalysis;
}

interface EventCardProps {
  event: EventData;
  compact?: boolean;
}

const tierConfig = {
  A: {
    label: "A-tier",
    description: "Peer-reviewed",
    color: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
  },
  B: {
    label: "B-tier",
    description: "Official lab",
    color: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
  },
  C: {
    label: "C-tier",
    description: "Press (if true)",
    color: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20",
  },
  D: {
    label: "D-tier",
    description: "Social media",
    color: "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20",
  },
};

const linkTypeIcons = {
  supports: { icon: CheckCircle2, color: "text-green-600 dark:text-green-400" },
  contradicts: { icon: AlertTriangle, color: "text-red-600 dark:text-red-400" },
  related: { icon: Clock, color: "text-blue-600 dark:text-blue-400" },
};

export function EventCard({ event, compact = false }: EventCardProps) {
  const [expanded, setExpanded] = useState(false);
  const tierInfo = tierConfig[event.evidence_tier];

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getSignificanceBadge = (score: number) => {
    if (score >= 0.9) return { label: "Major", color: "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20" };
    if (score >= 0.7) return { label: "Significant", color: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20" };
    if (score >= 0.5) return { label: "Incremental", color: "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20" };
    return { label: "Minor", color: "bg-gray-400/10 text-gray-600 dark:text-gray-500 border-gray-400/20" };
  };

  return (
    <Card className={`hover:shadow-lg transition-shadow ${event.retracted ? "opacity-60" : ""}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant="outline" className={tierInfo.color}>
                {tierInfo.label}
              </Badge>
              {event.analysis && (
                <Badge variant="outline" className={getSignificanceBadge(event.analysis.significance_score).color}>
                  {getSignificanceBadge(event.analysis.significance_score).label}
                </Badge>
              )}
              {event.provisional && (
                <Badge variant="outline" className="bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20">
                  Provisional
                </Badge>
              )}
              {event.needs_review && (
                <Badge variant="outline" className="bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20">
                  Needs Review
                </Badge>
              )}
              {event.retracted && (
                <Badge variant="outline" className="bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20">
                  Retracted
                </Badge>
              )}
            </div>
            <CardTitle className={`text-xl mb-1 ${event.retracted ? "line-through" : ""}`}>
              {event.title}
            </CardTitle>
            <CardDescription className="text-sm">
              {event.publisher} • {formatDate(event.published_at)}
            </CardDescription>
          </div>
          <SafeLink
            href={event.source_url}
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          >
            <ExternalLink className="h-5 w-5" />
          </SafeLink>
        </div>
      </CardHeader>

      <CardContent>
        {/* Retraction Banner (Sprint 6.1) */}
        {event.retracted && (
          <div className="mb-4">
            <RetractionBanner
              retractedAt={event.retracted_at}
              reason={event.retraction_reason}
              evidenceUrl={event.retraction_evidence_url}
            />
          </div>
        )}

        {/* Sprint 10: URL Validation Warning */}
        {event.url_is_valid === false && (
          <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm">
                <p className="font-medium text-yellow-800 dark:text-yellow-400 mb-1">
                  Source link may be unavailable
                </p>
                <p className="text-yellow-700 dark:text-yellow-500 text-xs">
                  {event.url_error || `Link returned HTTP ${event.url_status_code}`}
                  {event.url_validated_at && (
                    <span className="text-yellow-600 dark:text-yellow-600">
                      {" "}• Checked {formatDate(event.url_validated_at)}
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Event Summary */}
        {!compact && event.summary && (
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">{event.summary}</p>
        )}

        {/* Signpost Links */}
        {event.signpost_links && event.signpost_links.length > 0 && (
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
              Linked Signposts ({event.signpost_links.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {event.signpost_links.map((link) => {
                const linkType = link.link_type || "related";
                const LinkIcon = linkTypeIcons[linkType]?.icon || Clock;
                const iconColor = linkTypeIcons[linkType]?.color || "text-blue-600 dark:text-blue-400";
                return (
                  <Badge
                    key={link.signpost_id}
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    <LinkIcon className={`h-3 w-3 ${iconColor}`} />
                    {link.signpost_name}
                  </Badge>
                );
              })}
            </div>
          </div>
        )}

        {/* AI Analysis - "Why this matters" */}
        {event.analysis && (
          <div className="border-t pt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="w-full justify-between hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <span className="font-semibold text-sm">Why this matters</span>
              {expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>

            {expanded && (
              <div className="mt-3 space-y-4">
                {/* Summary */}
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {event.analysis.summary}
                  </p>
                </div>

                {/* Impact Areas */}
                {event.analysis.impact_json && (
                  <div className="space-y-2">
                    {event.analysis.impact_json.capabilities && (
                      <div className="bg-blue-50 dark:bg-blue-950/30 p-3 rounded-md">
                        <h5 className="text-xs font-semibold text-blue-900 dark:text-blue-300 mb-1">
                          Capabilities
                        </h5>
                        <p className="text-sm text-blue-800 dark:text-blue-400">
                          {event.analysis.impact_json.capabilities}
                        </p>
                      </div>
                    )}
                    {event.analysis.impact_json.timelines && (
                      <div className="bg-purple-50 dark:bg-purple-950/30 p-3 rounded-md">
                        <h5 className="text-xs font-semibold text-purple-900 dark:text-purple-300 mb-1">
                          Timelines
                        </h5>
                        <p className="text-sm text-purple-800 dark:text-purple-400">
                          {event.analysis.impact_json.timelines}
                        </p>
                      </div>
                    )}
                    {event.analysis.impact_json.safety_implications && (
                      <div className="bg-red-50 dark:bg-red-950/30 p-3 rounded-md">
                        <h5 className="text-xs font-semibold text-red-900 dark:text-red-300 mb-1">
                          Safety Implications
                        </h5>
                        <p className="text-sm text-red-800 dark:text-red-400">
                          {event.analysis.impact_json.safety_implications}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Relevance Details */}
                {event.analysis.relevance_explanation && (
                  <div className="text-xs text-gray-600 dark:text-gray-400 pt-2 border-t">
                    <details>
                      <summary className="cursor-pointer font-semibold hover:text-gray-900 dark:hover:text-gray-200">
                        Technical Details
                      </summary>
                      <p className="mt-2 leading-relaxed">{event.analysis.relevance_explanation}</p>
                    </details>
                  </div>
                )}

                {/* Significance Score */}
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-2 border-t">
                  <span>AI-generated analysis</span>
                  <span>Significance: {event.analysis.significance_score.toFixed(2)}/1.0</span>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
