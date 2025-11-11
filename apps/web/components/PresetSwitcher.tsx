'use client'

import { useRouter, useSearchParams } from 'next/navigation'

const PRESETS = [
  { value: 'equal', label: 'Equal' },
  { value: 'aschenbrenner', label: 'Aschenbrenner' },
  { value: 'ai2027', label: 'AI-2027' },
]

export function PresetSwitcher() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const currentPreset = searchParams.get('preset') || 'equal'
  
  const handlePresetChange = (preset: string) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('preset', preset)
    router.push(`?${params.toString()}`)
  }
  
  return (
    <div className="flex gap-2 p-1 bg-muted rounded-lg" data-testid="preset-switcher">
      {PRESETS.map((preset) => (
        <button
          key={preset.value}
          onClick={() => handlePresetChange(preset.value)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            currentPreset === preset.value
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-background'
          }`}
          data-testid={`preset-${preset.value}`}
        >
          {preset.label}
        </button>
      ))}
    </div>
  )
}

