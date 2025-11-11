/**
 * WeightSlider - Accessible range input for weight adjustment
 * Used in What-If Simulator
 */

import styles from './WeightSlider.module.css'

interface WeightSliderProps {
  label: string
  value: number  // 0-1
  onChange: (value: number) => void
  min?: number
  max?: number
}

export function WeightSlider({ 
  label, 
  value, 
  onChange, 
  min = 0, 
  max = 1 
}: WeightSliderProps) {
  const percentage = Math.round(value * 100)
  
  return (
    <label className={styles.wrap}>
      <span className={styles.label}>{label}</span>
      <input
        type="range"
        min={min * 100}
        max={max * 100}
        value={percentage}
        onChange={(e) => onChange(parseInt(e.currentTarget.value, 10) / 100)}
        aria-label={`${label} weight`}
        className={styles.slider}
      />
      <output className={styles.output}>{percentage}%</output>
    </label>
  )
}

