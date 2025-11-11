"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface SecurityLevel {
  level: number
  label: string
  description: string
  achieved: boolean
}

interface SecurityLadderProps {
  maturityScore: number  // 0..1
  levels?: SecurityLevel[]
}

const DEFAULT_LEVELS: SecurityLevel[] = [
  {
    level: 0,
    label: "L0: Baseline",
    description: "Basic security practices",
    achieved: true,
  },
  {
    level: 1,
    label: "L1: Model Weights",
    description: "Secured model weights with access controls",
    achieved: false,
  },
  {
    level: 2,
    label: "L2: Inference Monitoring",
    description: "Real-time monitoring for misuse detection",
    achieved: false,
  },
  {
    level: 3,
    label: "L3: State-Actor Resistant",
    description: "Security posture resistant to state-level threats",
    achieved: false,
  },
]

export function SecurityLadder({ 
  maturityScore, 
  levels = DEFAULT_LEVELS 
}: SecurityLadderProps) {
  // Determine current level from maturity score
  const currentLevel = Math.floor(maturityScore * (levels.length - 1))
  
  // Update achieved status based on current level
  const updatedLevels = levels.map((level, idx) => ({
    ...level,
    achieved: idx <= currentLevel,
  }))

  return (
    <Card data-testid="security-maturity">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Security Maturity Ladder</CardTitle>
            <CardDescription>
              Current maturity: {(maturityScore * 100).toFixed(1)}% (Level {currentLevel})
            </CardDescription>
          </div>
          <div className="text-3xl font-bold text-primary">
            {(maturityScore * 100).toFixed(0)}%
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Visual ladder */}
          <div className="relative pl-8">
            {updatedLevels.map((level, idx) => (
              <div key={idx} className="relative pb-8 last:pb-0">
                {/* Connector line */}
                {idx < updatedLevels.length - 1 && (
                  <div 
                    className={`absolute left-0 top-6 w-0.5 h-full ${
                      level.achieved ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                    style={{ marginLeft: '11px' }}
                  />
                )}
                
                {/* Level indicator */}
                <div className="flex items-start gap-4">
                  <div 
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold ${
                      level.achieved 
                        ? 'bg-green-500 border-green-500 text-white' 
                        : 'bg-white border-gray-300 text-gray-400'
                    }`}
                  >
                    {level.level}
                  </div>
                  
                  <div className="flex-1 pt-0.5">
                    <div className="flex items-center gap-2">
                      <div className="font-semibold text-sm">{level.label}</div>
                      <Badge 
                        variant={level.achieved ? "default" : "outline"}
                        className={`text-xs ${level.achieved ? 'bg-green-600' : ''}`}
                      >
                        {level.achieved ? 'Achieved' : 'Pending'}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {level.description}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Maturity bar */}
          <div className="mt-6">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                style={{ width: `${maturityScore * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span>L0</span>
              <span>L1</span>
              <span>L2</span>
              <span>L3</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

