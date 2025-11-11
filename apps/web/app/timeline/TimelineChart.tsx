/**
 * TimelineChart component - Extracted for code splitting (Sprint 9)
 * Heavy Recharts import is lazy-loaded on demand
 */
import React from "react";
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Badge } from "@/components/ui/badge";

const tierColors = {
  A: "#10b981", // green
  B: "#3b82f6", // blue
  C: "#eab308", // yellow
  D: "#6b7280", // gray
};

interface TimelineChartProps {
  timelineData: any[];
  viewMode: "scatter" | "cumulative";
}

export default function TimelineChart({ timelineData, viewMode }: TimelineChartProps) {
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;

      if (viewMode === "scatter") {
        return (
          <div className="bg-white dark:bg-gray-800 border rounded-lg p-3 shadow-lg max-w-xs">
            <Badge variant="outline" className="mb-2">
              {data.tier}-tier
            </Badge>
            <p className="font-semibold text-sm mb-1">{data.title}</p>
            <p className="text-xs text-gray-600 dark:text-gray-400">{data.dateLabel}</p>
            <p className="text-xs mt-2">
              Significance: <strong>{data.significance.toFixed(2)}</strong>
            </p>
          </div>
        );
      } else {
        return (
          <div className="bg-white dark:bg-gray-800 border rounded-lg p-3 shadow-lg">
            <p className="font-semibold text-sm">{data.dateLabel}</p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Total events: <strong>{data.count}</strong>
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Avg significance: <strong>{data.avgSignificance.toFixed(2)}</strong>
            </p>
          </div>
        );
      }
    }
    return null;
  };

  if (timelineData.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-900 border rounded-lg p-6">
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Loading timeline data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-900 border rounded-lg p-6">
      {viewMode === "scatter" ? (
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              type="number"
              domain={["auto", "auto"]}
              tickFormatter={(timestamp) =>
                new Date(timestamp).toLocaleDateString(undefined, { month: "short", year: "2-digit" })
              }
              label={{ value: "Publication Date", position: "insideBottom", offset: -10 }}
            />
            <YAxis
              dataKey="significance"
              domain={[0, 1]}
              label={{ value: "Significance Score", angle: -90, position: "insideLeft" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Scatter name="Events" data={timelineData} fill="#8884d8">
              {timelineData.map((entry: any, index: number) => (
                <Cell key={`cell-${index}`} fill={tierColors[entry.tier as keyof typeof tierColors]} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={500}>
          <LineChart data={timelineData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              type="number"
              domain={["auto", "auto"]}
              tickFormatter={(timestamp) =>
                new Date(timestamp).toLocaleDateString(undefined, { month: "short", year: "2-digit" })
              }
              label={{ value: "Publication Date", position: "insideBottom", offset: -10 }}
            />
            <YAxis
              yAxisId="left"
              label={{ value: "Cumulative Event Count", angle: -90, position: "insideLeft" }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 1]}
              label={{ value: "Avg Significance", angle: 90, position: "insideRight" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Event Count"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="avgSignificance"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="Avg Significance"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
