/**
 * StoryCard - Editorial card for weekly narratives
 * Newsroom kicker + headline + deck pattern
 */

import Link from 'next/link'
import styles from './StoryCard.module.css'

interface StoryCardProps {
  slug: string
  title: string
  deck?: string
  kicker?: string
  date: string
  readingMinutes?: number
}

export function StoryCard({ 
  slug, 
  title, 
  deck, 
  kicker = 'This Week in AGI', 
  date, 
  readingMinutes = 4 
}: StoryCardProps) {
  return (
    <article className={styles.card}>
      <div className={styles.kicker}>{kicker}</div>
      <h3 className={styles.title}>
        <Link href={`/stories/${slug}`}>{title}</Link>
      </h3>
      {deck && <p className={styles.deck}>{deck}</p>}
      <div className={styles.meta}>
        <time dateTime={date}>
          {new Date(date).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
          })}
        </time>
        <span aria-hidden="true">•</span>
        <span>{readingMinutes} min read</span>
      </div>
    </article>
  )
}

