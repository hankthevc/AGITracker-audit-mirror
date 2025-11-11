import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SecurityLadder } from '@/components/SecurityLadder'
import { Badge } from '@/components/ui/badge'

export default function SecurityPage() {
  // Sample maturity score - in production, fetch from /v1/index security value
  // or from /v1/signposts/by-code/sec_maturity
  const maturityScore = 0.35  // 35% maturity (between L1 and L2)

  const securitySignals = [
    {
      name: "HSM-Protected Model Weights",
      description: "Model weights secured with hardware security modules against exfiltration",
      tier: "A",
      status: "Implemented"
    },
    {
      name: "Regular Red Team Exercises",
      description: "Documented red team exercises for vulnerability and misuse detection",
      tier: "A",
      status: "Ongoing"
    },
    {
      name: "Insider Threat Program",
      description: "Comprehensive insider threat monitoring and mitigation procedures",
      tier: "B",
      status: "In Progress"
    },
    {
      name: "External Security Audit",
      description: "Third-party security audit with public attestation",
      tier: "A",
      status: "Planned"
    },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Security Posture</h1>
        <p className="text-xl text-muted-foreground">
          Tracking security maturity and governance development
        </p>
      </div>
      
      {/* Security Maturity Ladder */}
      <SecurityLadder maturityScore={maturityScore} />

      {/* Security Signals */}
      <Card>
        <CardHeader>
          <CardTitle>Security Signals (A/B Tier)</CardTitle>
          <CardDescription>
            Evidence-based security indicators from frontier AI labs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {securitySignals.map((signal, idx) => (
              <div key={idx} className="flex items-start justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium">{signal.name}</h3>
                    <Badge 
                      variant={signal.tier === 'A' ? 'default' : 'secondary'}
                      className={signal.tier === 'A' ? 'bg-green-600' : 'bg-blue-600'}
                    >
                      Tier {signal.tier}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{signal.description}</p>
                </div>
                <Badge variant="outline" className="ml-4">
                  {signal.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Methodology */}
      <Card>
        <CardHeader>
          <CardTitle>Security Maturity Methodology</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong>A/B Tier Signals Only:</strong> Security maturity score is computed from verified (A-tier) 
            and credible (B-tier) evidence only. C/D tier signals are shown as "provisional" and do not affect the score.
          </p>
          <p>
            <strong>Weighted Aggregation:</strong> Each signal contributes to overall maturity based on its importance 
            weight and maturity contribution. The final score is a weighted average from 0 (baseline) to 1 (state-actor resistant).
          </p>
          <p>
            <strong>Level Progression:</strong> L0 (Baseline) → L1 (Model Weights Secured) → L2 (Inference Monitoring) → 
            L3 (State-Actor Resistant). Each level requires progressively stronger security controls.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

