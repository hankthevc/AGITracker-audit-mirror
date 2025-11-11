"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Milestone {
  label: string
  value: number
  unit: string
  achieved: boolean
  date?: string
}

interface OOMMeterProps {
  milestones: Milestone[]
  title?: string
  description?: string
}

export function OOMMeter({ 
  milestones, 
  title = "Inputs OOM Milestones",
  description = "Orders of magnitude progress in training compute, DC power, and algorithmic efficiency"
}: OOMMeterProps) {
  // Log scale visualization
  const getLogPosition = (value: number, min: number, max: number) => {
    const logValue = Math.log10(value)
    const logMin = Math.log10(min)
    const logMax = Math.log10(max)
    return ((logValue - logMin) / (logMax - logMin)) * 100
  }

  // Determine range from milestones
  const values = milestones.map(m => m.value)
  const minValue = Math.min(...values) / 10 // Start one OOM below
  const maxValue = Math.max(...values) * 10 // End one OOM above

  return (
    <Card data-testid="oom-meter">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Log scale bar */}
          <div className="relative h-12 bg-muted rounded-lg">
            <div className="absolute inset-0 flex items-center px-4">
              <div className="w-full h-1 bg-border relative">
                {milestones.map((milestone, idx) => {
                  const position = getLogPosition(milestone.value, minValue, maxValue)
                  return (
                    <div
                      key={idx}
                      className="absolute"
                      style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
                    >
                      <div 
                        className={`w-3 h-3 rounded-full -mt-1 ${
                          milestone.achieved 
                            ? 'bg-green-500' 
                            : 'bg-gray-400'
                        }`}
                        title={`${milestone.label}: ${milestone.value} ${milestone.unit}`}
                      />
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Milestone list */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {milestones.map((milestone, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border ${
                  milestone.achieved 
                    ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800' 
                    : 'bg-muted border-border'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{milestone.label}</div>
                    <div className="text-xs text-muted-foreground">
                      {milestone.value.toExponential(0)} {milestone.unit}
                    </div>
                  </div>
                  <Badge 
                    variant={milestone.achieved ? "default" : "outline"}
                    className={milestone.achieved ? "bg-green-600" : ""}
                  >
                    {milestone.achieved ? '✓' : '○'}
                  </Badge>
                </div>
                {milestone.date && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {milestone.achieved ? 'Achieved' : 'Projected'}: {milestone.date}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="text-sm text-center text-muted-foreground">
            {milestones.filter(m => m.achieved).length} of {milestones.length} milestones achieved
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
