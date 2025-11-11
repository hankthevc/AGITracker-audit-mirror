'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Milestone {
  id: string
  name: string
  targetDate: string
  actualDate?: string
  status: 'ahead' | 'on-track' | 'behind' | 'pending'
}

interface ScenarioTimelineProps {
  milestones: Milestone[]
  scenarioName?: string
}

export function ScenarioTimeline({ milestones, scenarioName = "AI 2027" }: ScenarioTimelineProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ahead':
        return 'bg-green-600'
      case 'on-track':
        return 'bg-blue-600'
      case 'behind':
        return 'bg-red-600'
      case 'pending':
        return 'bg-gray-400'
      default:
        return 'bg-gray-400'
    }
  }
  
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ahead':
        return 'Ahead'
      case 'on-track':
        return 'On Track'
      case 'behind':
        return 'Behind'
      case 'pending':
        return 'Pending'
      default:
        return 'Unknown'
    }
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{scenarioName} Timeline</CardTitle>
        <CardDescription>Milestone progress tracking</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300" />
          
          {/* Milestones */}
          <div className="space-y-8">
            {milestones.map((milestone, index) => (
              <div key={milestone.id} className="relative pl-16">
                {/* Timeline dot */}
                <div
                  className={`absolute left-6 top-2 w-4 h-4 rounded-full border-4 border-white ${
                    milestone.status === 'pending' ? 'bg-gray-300' : 'bg-primary'
                  }`}
                />
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="font-semibold">{milestone.name}</h4>
                    <Badge className={getStatusColor(milestone.status)}>
                      {getStatusLabel(milestone.status)}
                    </Badge>
                  </div>
                  
                  <div className="text-sm text-muted-foreground space-y-1">
                    <div>Target: {milestone.targetDate}</div>
                    {milestone.actualDate && (
                      <div>Actual: {milestone.actualDate}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

