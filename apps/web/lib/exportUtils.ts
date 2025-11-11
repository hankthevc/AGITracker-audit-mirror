/**
 * Export utilities for different formats
 * 
 * ✅ FIX: Dynamic imports to avoid bundling large libraries
 */

export interface ExportEvent {
  id: number
  title: string
  publisher: string
  published_at: string
  tier: string
  summary?: string
  url?: string
}

/**
 * Export events to Excel (.xlsx)
 * Uses dynamic import to avoid bundling ~1MB library upfront
 */
export async function exportToExcel(events: ExportEvent[], filename: string = 'events-export') {
  // ✅ FIX: Dynamic import - only loads when user exports
  const XLSX = await import('xlsx')
  
  const worksheet = XLSX.utils.json_to_sheet(
    events.map(event => ({
      ID: event.id,
      Title: event.title,
      Publisher: event.publisher,
      'Published Date': new Date(event.published_at).toLocaleDateString(),
      Tier: event.tier,
      Summary: event.summary || '',
      URL: event.url || '',
    }))
  )
  
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Events')
  
  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

/**
 * Export events to CSV
 * Uses dynamic import to avoid bundling ~1MB library upfront
 */
export async function exportToCSV(events: ExportEvent[], filename: string = 'events-export') {
  // ✅ FIX: Dynamic import
  const XLSX = await import('xlsx')
  
  const worksheet = XLSX.utils.json_to_sheet(
    events.map(event => ({
      ID: event.id,
      Title: event.title,
      Publisher: event.publisher,
      'Published Date': new Date(event.published_at).toLocaleDateString(),
      Tier: event.tier,
      Summary: event.summary || '',
      URL: event.url || '',
    }))
  )
  
  const csv = XLSX.utils.sheet_to_csv(worksheet)
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * Export events to iCal format
 */
export function exportToICal(events: ExportEvent[], filename: string = 'events-export') {
  const icalEvents = events.map((event) => {
    const dtStart = new Date(event.published_at).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    const dtStamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    
    return [
      'BEGIN:VEVENT',
      `DTSTART:${dtStart}`,
      `DTSTAMP:${dtStamp}`,
      `SUMMARY:${event.title.replace(/,/g, '\\,')}`,
      `DESCRIPTION:${(event.summary || '').replace(/,/g, '\\,').substring(0, 200)}`,
      `CATEGORIES:Tier ${event.tier},${event.publisher}`,
      `UID:${event.id}@agi-tracker`,
      event.url ? `URL:${event.url}` : '',
      'END:VEVENT',
    ].filter(line => line).join('\r\n')
  }).join('\r\n')
  
  const icalContent = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//AGI Signpost Tracker//Events//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'X-WR-CALNAME:AGI Events',
    'X-WR-TIMEZONE:UTC',
    icalEvents,
    'END:VCALENDAR',
  ].join('\r\n')
  
  const blob = new Blob([icalContent], { type: 'text/calendar;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.ics`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * Export events to JSON
 */
export function exportToJSON(events: ExportEvent[], filename: string = 'events-export') {
  const json = JSON.stringify(events, null, 2)
  
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.json`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * Copy data to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    return false
  }
}

