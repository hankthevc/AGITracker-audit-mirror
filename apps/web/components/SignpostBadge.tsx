/**
 * SignpostBadge - Chip displaying signpost code
 */

import styles from './SignpostBadge.module.css'

interface SignpostBadgeProps {
  code: string
}

export function SignpostBadge({ code }: SignpostBadgeProps) {
  return <span className={styles.badge}>{code}</span>
}

