import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function AschenbrennerRoadmapPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          Aschenbrenner's Situational Awareness Roadmap
        </h1>
        <p className="text-xl text-muted-foreground">
          Focus on OOMs of effective compute, algorithmic unhobbling, and security posture
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Preset Weights</CardTitle>
          <CardDescription>Category weighting for this roadmap</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">40%</div>
              <div className="text-sm text-muted-foreground">Inputs</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">30%</div>
              <div className="text-sm text-muted-foreground">Agents</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">20%</div>
              <div className="text-sm text-muted-foreground">Capabilities</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">10%</div>
              <div className="text-sm text-muted-foreground">Security</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Key Theses</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <h3>1. OOMs Matter Most</h3>
          <p>
            Progress toward AGI is primarily determined by orders of magnitude improvements in
            effective compute—combining both raw compute (FLOP) and algorithmic efficiency gains.
          </p>
          
          <h3>2. Unhobbling Agents</h3>
          <p>
            Current models already have significant latent capabilities. The key bottleneck is
            "unhobbling"—removing artificial constraints and enabling effective agentic behavior
            through better scaffolding, tool use, and multi-step reasoning.
          </p>
          
          <h3>3. Security Lags Capabilities</h3>
          <p>
            Security and safety measures are currently far behind capability advancement. This
            creates an increasing risk as models approach transformative thresholds.
          </p>
          
          <h3>4. Timeline: 2027 AGI</h3>
          <p>
            If current trends continue (4-5 OOM effective compute improvement 2023-2027), we
            could reach AGI-level systems by 2027. This requires both scaling and unhobbling.
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Priority Signposts</CardTitle>
          <CardDescription>Key metrics for this roadmap</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">▸</span>
              <div>
                <strong>Training Compute 10^26-10^27 FLOP:</strong> Critical threshold for
                transformative AI capabilities
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">▸</span>
              <div>
                <strong>Algorithmic Efficiency +2 OOM:</strong> Expected improvement through
                better architectures and training methods
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">▸</span>
              <div>
                <strong>Agent Reliability 80%:</strong> Unhobbling threshold for economically
                useful autonomous agents
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">▸</span>
              <div>
                <strong>Multi-day Projects:</strong> Capability to complete complex, multi-step
                tasks with minimal supervision
              </div>
            </li>
          </ul>
        </CardContent>
      </Card>
      
      <Card className="border-yellow-200 bg-yellow-50">
        <CardHeader>
          <CardTitle>Security Concerns</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>
            This roadmap emphasizes the growing gap between capabilities and security readiness.
            Key risks include:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Model weight exfiltration by state actors</li>
            <li>Insufficient inference-time monitoring for misuse</li>
            <li>Race dynamics preventing adequate safety measures</li>
            <li>Lack of international coordination on compute governance</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

