import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AI2027Timeline } from '@/components/AI2027Timeline'

export default function AI2027RoadmapPage() {
  // Sample timeline items - in production, fetch from /v1/signposts/by-code/{code}/predictions
  // and compute ahead/on/behind status based on current date vs target_date
  const timelineItems = [
    {
      id: 'ai2027_flops_26',
      label: '1e26 FLOP Training Run',
      signpost_code: 'inputs_flops_26',
      target_date: '2025-03-01',
      confidence: 'high',
      rationale: 'First 1e26 FLOP training run expected by early 2025 based on current buildout',
      observed_date: '2024-10-01',  // Example: achieved early
      current_value: 1.0,
      status: 'ahead' as const,
    },
    {
      id: 'ai2027_swe_70',
      label: 'Agentic Coding 70%',
      signpost_code: 'swe_bench_85',
      target_date: '2025-06-01',
      confidence: 'high',
      rationale: 'AI 2027 predicts autonomous coding agents achieving 70%+ on real-world GitHub issues by mid-2025',
      current_value: 0.68,
      status: 'on_track' as const,
    },
    {
      id: 'ai2027_osworld_65',
      label: 'OS-Level Tasks 65%',
      signpost_code: 'osworld_65',
      target_date: '2025-09-01',
      confidence: 'medium',
      rationale: 'Complex OS-level task automation reaching 65% success by late 2025',
      status: 'pending' as const,
    },
    {
      id: 'ai2027_dc_1gw',
      label: '1 GW Datacenter',
      signpost_code: 'inputs_dc_1gw',
      target_date: '2025-12-01',
      confidence: 'high',
      rationale: 'First 1 GW AI datacenter cluster expected by end of 2025 (xAI, Meta commitments)',
      status: 'pending' as const,
    },
    {
      id: 'ai2027_webarena_70',
      label: 'Web Navigation 70%',
      signpost_code: 'webarena_70',
      target_date: '2025-12-01',
      confidence: 'medium',
      rationale: 'Autonomous web navigation and task completion reaching 70% by end of 2025',
      status: 'pending' as const,
    },
    {
      id: 'ai2027_gpqa_75',
      label: 'PhD-Level Science 75%',
      signpost_code: 'gpqa_sota',
      target_date: '2025-12-01',
      confidence: 'medium',
      rationale: 'PhD-level science question answering at 75% accuracy by end of 2025',
      status: 'pending' as const,
    },
    {
      id: 'ai2027_swe_85',
      label: 'Agentic Coding 85%',
      signpost_code: 'swe_bench_90',
      target_date: '2026-03-01',
      confidence: 'medium',
      rationale: 'Near-human expert performance on software engineering benchmarks expected by early 2026',
      status: 'pending' as const,
    },
    {
      id: 'ai2027_flops_27',
      label: '1e27 FLOP Training Run',
      signpost_code: 'inputs_flops_27',
      target_date: '2026-06-01',
      confidence: 'high',
      rationale: 'Scaling to 1e27 FLOPs projected for mid-2026 based on current buildout',
      status: 'pending' as const,
    },
    {
      id: 'ai2027_job_displacement',
      label: '10% Job Displacement',
      signpost_code: 'economic_displacement_10pct',
      target_date: '2026-12-01',
      confidence: 'medium',
      rationale: 'Economic displacement of 10% of remote knowledge work projected for late 2026',
      status: 'pending' as const,
    },
  ]
  
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">AI 2027 Scenario Roadmap</h1>
        <p className="text-xl text-muted-foreground">
          Timeline-aligned signposts for near-term AGI scenarios
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
              <div className="text-3xl font-bold">35%</div>
              <div className="text-sm text-muted-foreground">Agents</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">30%</div>
              <div className="text-sm text-muted-foreground">Capabilities</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">25%</div>
              <div className="text-sm text-muted-foreground">Inputs</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold">10%</div>
              <div className="text-sm text-muted-foreground">Security</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <AI2027Timeline items={timelineItems} />
      
      <Card>
        <CardHeader>
          <CardTitle>Scenario Overview</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <p>
            The AI 2027 scenario projects that by 2027, AI systems will be capable of autonomously
            performing the majority of economically valuable remote cognitive work. This roadmap
            emphasizes near-term milestones and explicit timeline alignment.
          </p>
          
          <h3>Key Assumptions</h3>
          <ul>
            <li>Continued exponential improvement in benchmark performance (2023-2027)</li>
            <li>Successful "unhobbling" of agentic capabilities</li>
            <li>Sufficient compute availability (10^26-10^27 FLOP training runs)</li>
            <li>Rapid real-world deployment and economic integration</li>
          </ul>
          
          <h3>Critical Milestones</h3>
          <ul>
            <li>
              <strong>2025:</strong> SWE-bench Verified 70%, OSWorld 50% - demonstrating
              practical computer use at scale
            </li>
            <li>
              <strong>2026:</strong> Multi-week autonomous projects, 10% job displacement -
              economic impact becomes measurable
            </li>
            <li>
              <strong>2027:</strong> Combined threshold crossing on all first-class benchmarks -
              AGI operational definition satisfied
            </li>
          </ul>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Status Indicators</CardTitle>
          <CardDescription>Understanding timeline alignment</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-3">
              <div className="w-12 h-8 bg-green-600 rounded flex items-center justify-center text-white text-xs font-bold">
                Ahead
              </div>
              <div>Milestone reached earlier than projected timeline</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-8 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">
                On
              </div>
              <div>Progress tracking with timeline expectations</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-8 bg-red-600 rounded flex items-center justify-center text-white text-xs font-bold">
                Behind
              </div>
              <div>Progress slower than timeline projections</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

