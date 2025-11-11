"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface RetractionBannerProps {
  retractedAt?: string;
  reason?: string;
  evidenceUrl?: string;
}

export function RetractionBanner({
  retractedAt,
  reason,
  evidenceUrl,
}: RetractionBannerProps) {
  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return "Unknown date";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch {
      return "Unknown date";
    }
  };

  return (
    <Alert variant="destructive" className="border-red-500 bg-red-50 dark:bg-red-950/20">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle className="flex items-center gap-2">
        <span>This claim has been retracted</span>
        <Badge variant="destructive">Retracted</Badge>
      </AlertTitle>
      <AlertDescription className="mt-2 space-y-2">
        {retractedAt && (
          <p className="text-sm">
            <strong>Retracted on:</strong> {formatDate(retractedAt)}
          </p>
        )}
        {reason && (
          <p className="text-sm">
            <strong>Reason:</strong> {reason}
          </p>
        )}
        {evidenceUrl && (
          <>
            {/* eslint-disable-next-line no-restricted-syntax */}
            {/* Database-sourced retraction evidence URL */}
          <a
            href={evidenceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm inline-flex items-center gap-1 text-red-700 dark:text-red-400 hover:underline"
          >
            View retraction evidence
            <ExternalLink className="h-3 w-3" />
          </a>
          </>
        )}
        <p className="text-xs text-muted-foreground mt-2">
          This event is excluded from all gauge calculations and index computations.
        </p>
      </AlertDescription>
    </Alert>
  );
}
