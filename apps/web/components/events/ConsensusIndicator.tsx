"use client";

import { Badge } from "@/components/ui/badge";
import { HelpCircle } from "lucide-react";

interface ConsensusIndicatorProps {
  consensusScore?: number;
  highVariance?: boolean;
  modelCount?: number;
}

export function ConsensusIndicator({
  consensusScore,
  highVariance,
  modelCount,
}: ConsensusIndicatorProps) {
  // Don't show if no consensus data
  if (consensusScore === undefined || modelCount === undefined) {
    return null;
  }

  // Only show if multi-model analysis (2+ models)
  if (modelCount < 2) {
    return null;
  }

  const getConsensusBadge = () => {
    if (consensusScore >= 0.9) {
      return {
        label: "Strong Consensus",
        color: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
        description: "Multiple models strongly agree",
      };
    }
    if (consensusScore >= 0.7) {
      return {
        label: "Consensus",
        color: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
        description: "Multiple models generally agree",
      };
    }
    return {
      label: "High Variance",
      color: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20",
      description: "Models disagree - needs review",
    };
  };

  const badge = getConsensusBadge();

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className={badge.color}>
        <div className="flex items-center gap-1">
          <span>{badge.label}</span>
          <span className="text-xs opacity-70">({modelCount} models)</span>
        </div>
      </Badge>
      {highVariance && (
        <span
          className="text-xs text-muted-foreground flex items-center gap-1"
          title={badge.description}
        >
          <HelpCircle className="h-3 w-3" />
          Flagged for review
        </span>
      )}
    </div>
  );
}
