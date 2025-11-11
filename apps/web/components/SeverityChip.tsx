/**
 * SeverityChip - Visual severity indicator for incidents
 * 1=info, 2=low, 3=medium, 4=high, 5=critical
 */

import styles from './SeverityChip.module.css'

interface SeverityChipProps {
  value: 1 | 2 | 3 | 4 | 5
  label?: string
}

const SEVERITY_LABELS: Record<number, string> = {
  1: 'Info',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Critical'
}

export function SeverityChip({ value, label }: SeverityChipProps) {
  return (
    <span className={styles.chip} data-severity={value}>
      {label || SEVERITY_LABELS[value]}
    </span>
  )
}

