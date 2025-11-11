import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { OOMMeter } from '@/components/OOMMeter'

export default function ComputePage() {
  // Sample milestones - in production, fetch from /v1/evidence filtered by Inputs category
  const flopsMilestones = [
    { label: "1e25 FLOPs (GPT-4 era)", value: 1e25, unit: "FLOPs", achieved: true, date: "2023-03" },
    { label: "1e26 FLOPs", value: 1e26, unit: "FLOPs", achieved: false, date: "2024-Q4 (est)" },
    { label: "1e27 FLOPs", value: 1e27, unit: "FLOPs", achieved: false, date: "2026-Q2 (proj)" },
  ]

  const dcPowerMilestones = [
    { label: "0.1 GW", value: 0.1, unit: "GW", achieved: true, date: "2023-Q2" },
    { label: "1 GW", value: 1.0, unit: "GW", achieved: false, date: "2025-Q4 (proj)" },
    { label: "10 GW", value: 10.0, unit: "GW", achieved: false, date: "2027-Q4 (proj)" },
  ]

  const algoMilestones = [
    { label: "+1 OOM since 2020", value: 10, unit: "x", achieved: true, date: "2023-09" },
    { label: "+2 OOM since 2020", value: 100, unit: "x", achieved: false, date: "2025-Q2 (proj)" },
    { label: "+3 OOM since 2020", value: 1000, unit: "x", achieved: false, date: "2027-Q1 (proj)" },
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Compute & Inputs</h1>
        <p className="text-xl text-muted-foreground">
          Training compute, algorithmic efficiency, and infrastructure build-out
        </p>
      </div>
      
      {/* Training FLOPs */}
      <OOMMeter
        milestones={flopsMilestones}
        title="Training Compute Milestones"
        description="Single training run FLOPs milestones (1e24 → 1e27)"
      />

      {/* DC Power */}
      <OOMMeter
        milestones={dcPowerMilestones}
        title="Data Center Power"
        description="Committed DC power for AI training clusters (0.1 GW → 10 GW)"
      />

      {/* Algorithmic Efficiency */}
      <OOMMeter
        milestones={algoMilestones}
        title="Algorithmic Efficiency Gains"
        description="Orders of magnitude improvement in algorithmic efficiency since 2020"
      />

      {/* Methodology */}
      <Card>
        <CardHeader>
          <CardTitle>Methodology</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong>Training FLOPs:</strong> Measured from publicly reported training runs and Epoch AI estimates. 
            Tracks the increase in compute used for frontier model training.
          </p>
          <p>
            <strong>DC Power:</strong> Committed data center power for AI training clusters, from public announcements 
            and infrastructure buildout reports.
          </p>
          <p>
            <strong>Algorithmic Efficiency:</strong> Improvement in effective compute per dollar, measured as the 
            reduction in compute needed to achieve the same performance (Epoch AI methodology).
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

