import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SafeLink } from '@/lib/SafeLink'

export default function MethodologyPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Methodology</h1>
        <p className="text-xl text-muted-foreground">
          How we track AGI progress through evidence-based signposts
        </p>
      </div>

      {/* Evidence Tiers */}
      <Card>
        <CardHeader>
          <CardTitle>Evidence Credibility Tiers</CardTitle>
          <CardDescription>
            We classify all evidence by source credibility using a 4-tier system
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <Badge className="bg-green-600">A</Badge>
              <div>
                <p className="font-semibold">Peer-Reviewed Research</p>
                <p className="text-sm text-muted-foreground">
                  Published papers in top-tier conferences (NeurIPS, ICLR, ICML, etc.) with verified results.
                  Undergone rigorous peer review and reproducibility checks.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Badge className="bg-blue-600">B</Badge>
              <div>
                <p className="font-semibold">Official Benchmarks & Lab Reports</p>
                <p className="text-sm text-muted-foreground">
                  Publicly accessible leaderboards (HuggingFace, Papers with Code), official lab announcements.
                  Provisional until peer-reviewed or independently verified.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Badge variant="secondary">C</Badge>
              <div>
                <p className="font-semibold">Industry Claims</p>
                <p className="text-sm text-muted-foreground">
                  Company blog posts, product announcements, CEO statements. Not peer-reviewed.
                  Displayed for awareness but <strong>does not move the main gauges</strong>.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Badge variant="outline">D</Badge>
              <div>
                <p className="font-semibold">Rumors & Leaks</p>
                <p className="text-sm text-muted-foreground">
                  Unverified claims, Twitter threads, speculation. Explicitly marked and{' '}
                  <strong>never affects scores</strong>. Included only for context.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <p className="text-sm font-semibold mb-2">📊 Evidence Policy</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>✓ Tiers A & B move the main gauges and contribute to overall progress</li>
              <li>✗ Tiers C & D are displayed but do not affect scores</li>
              <li>⚠️  All evidence is timestamped and can be retracted if debunked</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Scoring & Aggregation */}
      <Card>
        <CardHeader>
          <CardTitle>Scoring & Aggregation</CardTitle>
          <CardDescription>
            How we convert evidence into progress percentages
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold text-lg mb-2">Signpost Progress</h3>
            <p className="text-sm text-muted-foreground mb-2">
              Each signpost has a defined baseline and target value. Progress is computed as:
            </p>
            <div className="bg-muted p-3 rounded font-mono text-sm">
              progress = (current - baseline) / (target - baseline)
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Clamped to [0, 1] range. If current value exceeds target, progress = 1.0 (100%).
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-lg mb-2">Category Aggregation (Harmonic Mean)</h3>
            <p className="text-sm text-muted-foreground mb-2">
              Categories (Capabilities, Agents, Inputs, Security) aggregate signpost progress using a{' '}
              <strong>harmonic mean</strong>, which penalizes imbalanced progress:
            </p>
            <div className="bg-muted p-3 rounded font-mono text-sm">
              harmonic_mean = n / Σ(1/xᵢ)
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              This ensures no single signpost can "carry" the category. All signposts must advance together.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-lg mb-2">Overall Index</h3>
            <p className="text-sm text-muted-foreground mb-2">
              The overall AGI proximity index is computed from category scores using weighted roadmap presets:
            </p>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
              <li><strong>Equal</strong>: All categories weighted equally (25% each)</li>
              <li><strong>Aschenbrenner (Situational Awareness)</strong>: Capabilities 40%, Agents 30%, Inputs 20%, Security 10%</li>
              <li><strong>AI 2027</strong>: Custom weights based on Leopold Aschenbrenner's AGI timeline</li>
            </ul>
          </div>

          <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm font-semibold mb-2">⚠️  The N/A Rule</p>
            <p className="text-sm text-muted-foreground">
              Until <strong>both Inputs and Security</strong> categories have at least one A/B-tier signpost with non-zero progress,
              they are marked as <strong>N/A</strong> and do not contribute to the overall index. This prevents premature AGI proximity claims
              when foundational infrastructure (compute, data centers, security) is not yet in place.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Confidence Bands */}
      <Card>
        <CardHeader>
          <CardTitle>Confidence Bands</CardTitle>
          <CardDescription>
            Uncertainty quantification for the overall index
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">
            The overall index includes a ±10% confidence band to reflect measurement uncertainty, model disagreement,
            and the inherent difficulty of predicting AGI timelines.
          </p>
          <div className="bg-muted p-3 rounded text-sm">
            <p className="font-mono">confidence_lower = max(0, overall - 0.10)</p>
            <p className="font-mono">confidence_upper = min(1, overall + 0.10)</p>
          </div>
          <p className="text-sm text-muted-foreground mt-3">
            These bands widen when evidence is sparse or contradictory, and narrow as consensus emerges.
          </p>
        </CardContent>
      </Card>

      {/* HLE Monitor-Only Benchmark */}
      <Card className="border-orange-200 bg-orange-50/30">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CardTitle>Humanity&apos;s Last Exam (HLE) - Monitor-Only Benchmark</CardTitle>
            <Badge variant="secondary" className="bg-orange-100 text-orange-800">Provisional</Badge>
          </div>
          <CardDescription>
            Long-horizon PhD-level reasoning benchmark with strict quality gating
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            HLE is a PhD-level reasoning breadth benchmark tracking long-horizon capabilities (2026-2028 horizon). 
            Currently classified as <strong>monitor-only</strong> and does not affect main gauges.
          </p>

          <div className="space-y-2">
            <h4 className="font-semibold text-sm">📋 Benchmark Details</h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
              <li><strong>Versioning:</strong> Text-only variant (2,500 questions)</li>
              <li><strong>Evidence Tier:</strong> B (Provisional) - company-run leaderboard, not peer-reviewed</li>
              <li><strong>Signposts:</strong> hle_text_50 (≥50%), hle_text_70 (≥70%) - calibrated for 2026-2028 horizon</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-sm">⚠️  A-tier Upgrade Criteria</h4>
            <p className="text-sm text-muted-foreground">
              HLE evidence will be upgraded to A-tier (affecting main gauges) only when <strong>one of</strong> these conditions is met:
            </p>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
              <li>Peer-reviewed independent reproduction of results published</li>
              <li>Official label-quality remediation from CAIS/Scale addressing Bio/Chem subset issues</li>
            </ul>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <p className="text-sm font-semibold text-yellow-800 mb-1">🔬 Label Quality</p>
            <p className="text-xs text-yellow-800">
              Bio/Chem subsets have known issues per independent audits. We track HLE for long-term monitoring 
              but maintain strict quality standards before allowing it to influence main AGI proximity scores.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Safety Margin */}
      <Card>
        <CardHeader>
          <CardTitle>Safety Margin</CardTitle>
          <CardDescription>
            Tracking the gap between capability and security progress
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">
            The Safety Margin measures whether security measures are keeping pace with capability advances:
          </p>
          <div className="bg-muted p-3 rounded font-mono text-sm mb-3">
            safety_margin = security_progress - capability_progress
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-muted-foreground">
                <strong>Positive margin</strong>: Security ahead (safer trajectory)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-muted-foreground">
                <strong>Near zero</strong>: Capabilities and security in balance
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-muted-foreground">
                <strong>Negative margin</strong>: Capability sprint (higher risk)
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Sources */}
      <Card>
        <CardHeader>
          <CardTitle>Data Sources & Updates</CardTitle>
          <CardDescription>
            How we keep the tracker current
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="text-sm text-muted-foreground space-y-2">
            <li>
              <strong>Automated connectors</strong>: Daily scrapes of public leaderboards (SWE-bench, OSWorld, WebArena, GPQA)
            </li>
            <li>
              <strong>Manual curation</strong>: Weekly review of arXiv, HuggingFace, Papers with Code, and major lab announcements
            </li>
            <li>
              <strong>Community contributions</strong>: Submit evidence via GitHub issues with source links and tier justification
            </li>
            <li>
              <strong>Retractions</strong>: Claims can be retracted by admins if debunked or corrected, with full audit trail
            </li>
          </ul>
          <p className="text-sm text-muted-foreground mt-4">
            All raw data and scoring logic is open-source at{' '}
            <SafeLink 
              href="https://github.com/hankthevc/AGITracker" 
              className="text-primary hover:underline"
            >
              github.com/hankthevc/AGITracker
            </SafeLink>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
