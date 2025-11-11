"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface DigestData {
  filename: string;
  headline: string;
  key_moves: string[];
  what_it_means: string;
  velocity_assessment: string;
  outlook: string;
  surprise_factor: string | number;
  week_start: string;
  week_end: string;
  generated_at: string;
  num_events: number;
  tier_breakdown?: {
    A: number;
    B: number;
    C: number;
  };
  top_events?: Array<{
    id: string;
    title: string;
    evidence_tier: string;
    publisher: string;
  }>;
}

interface DigestsResponse {
  digests: DigestData[];
  count: number;
}

export default function DigestsPage() {
  const [digests, setDigests] = useState<DigestData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDigests = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "https://agitracker-production-6efa.up.railway.app"}/v1/digests?limit=12`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data: DigestsResponse = await response.json();
        setDigests(data.digests);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load digests");
      } finally {
        setLoading(false);
      }
    };

    fetchDigests();
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const getSurpriseColor = (surprise: string | number): string => {
    const score = typeof surprise === "string" ? parseFloat(surprise) : surprise;
    if (score >= 8) return "text-red-500";
    if (score >= 5) return "text-orange-500";
    if (score >= 3) return "text-yellow-500";
    return "text-green-500";
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-4xl font-bold mb-2">Weekly Digests</h1>
        <p className="text-muted-foreground mb-8">
          AI-generated summaries of AGI progress
        </p>
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6">
              <Skeleton className="h-6 w-3/4 mb-4" />
              <Skeleton className="h-4 w-1/4 mb-4" />
              <Skeleton className="h-20 w-full" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-4xl font-bold mb-8">Weekly Digests</h1>
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (digests.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-4xl font-bold mb-2">Weekly Digests</h1>
        <p className="text-muted-foreground mb-8">
          AI-generated summaries of AGI progress
        </p>
        <Alert>
          <AlertDescription>
            No digests available yet. Check back after Sunday when the weekly
            digest is generated.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Weekly Digests</h1>
        <p className="text-muted-foreground">
          AI-generated summaries of the most significant AGI progress each week
        </p>
      </div>

      <div className="space-y-8">
        {digests.map((digest) => (
          <Card key={digest.filename} className="p-6 hover:shadow-lg transition-shadow">
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline">
                    {digest.week_start ? formatDate(digest.week_start) : ""}
                  </Badge>
                  {digest.tier_breakdown && (
                    <div className="flex gap-1">
                      {digest.tier_breakdown.A > 0 && (
                        <Badge variant="default" className="bg-green-500">
                          {digest.tier_breakdown.A} A-tier
                        </Badge>
                      )}
                      {digest.tier_breakdown.B > 0 && (
                        <Badge variant="default" className="bg-blue-500">
                          {digest.tier_breakdown.B} B-tier
                        </Badge>
                      )}
                      {digest.tier_breakdown.C > 0 && (
                        <Badge variant="secondary">
                          {digest.tier_breakdown.C} C-tier
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-foreground">
                  {digest.headline}
                </h2>
              </div>
              {digest.surprise_factor && (
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">Surprise</div>
                  <div
                    className={`text-3xl font-bold ${getSurpriseColor(
                      digest.surprise_factor
                    )}`}
                  >
                    {typeof digest.surprise_factor === "string"
                      ? digest.surprise_factor
                      : digest.surprise_factor.toFixed(1)}
                  </div>
                </div>
              )}
            </div>

            {/* Key Moves */}
            {digest.key_moves && digest.key_moves.length > 0 && (
              <div className="mb-4">
                <h3 className="font-semibold mb-2">Key Developments</h3>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  {digest.key_moves.map((move, idx) => (
                    <li key={idx}>{move}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* What It Means */}
            {digest.what_it_means && (
              <div className="mb-4">
                <h3 className="font-semibold mb-2">Analysis</h3>
                <p className="text-muted-foreground whitespace-pre-wrap">
                  {digest.what_it_means}
                </p>
              </div>
            )}

            {/* Velocity Assessment */}
            {digest.velocity_assessment && (
              <div className="mb-4">
                <h3 className="font-semibold mb-2">Progress Assessment</h3>
                <p className="text-muted-foreground">{digest.velocity_assessment}</p>
              </div>
            )}

            {/* Outlook */}
            {digest.outlook && (
              <div className="mb-4">
                <h3 className="font-semibold mb-2">What to Watch</h3>
                <p className="text-muted-foreground">{digest.outlook}</p>
              </div>
            )}

            {/* Top Events */}
            {digest.top_events && digest.top_events.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <h3 className="font-semibold mb-2">Featured Events</h3>
                <div className="space-y-2">
                  {digest.top_events.map((event) => (
                    <div key={event.id} className="flex items-start gap-2">
                      <Badge variant="outline">{event.evidence_tier}</Badge>
                      <div className="flex-1">
                        <Link
                          href={`/events?id=${event.id}`}
                          className="text-sm hover:underline"
                        >
                          {event.title}
                        </Link>
                        <p className="text-xs text-muted-foreground">
                          {event.publisher}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
              Generated on {formatDate(digest.generated_at)} • {digest.num_events}{" "}
              events analyzed
            </div>
          </Card>
        ))}
      </div>

      {digests.length >= 12 && (
        <div className="mt-8 text-center text-muted-foreground">
          Showing the most recent 12 weeks of digests
        </div>
      )}
    </div>
  );
}
