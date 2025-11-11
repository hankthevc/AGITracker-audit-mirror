import { Metadata } from 'next'
import { WhatIfSimulator } from '@/components/WhatIfSimulator'

export const metadata: Metadata = {
  title: 'What-If Simulator | AGI Tracker',
  description: 'Interactive simulator to explore how different weight scenarios affect the AGI Progress Index',
}

export default function SimulatePage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <WhatIfSimulator />
    </div>
  )
}

