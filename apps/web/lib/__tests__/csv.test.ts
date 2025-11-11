/**
 * CSV Security Tests - BLOCKING in CI
 * 
 * These tests MUST pass to prevent CSV formula injection vulnerabilities.
 */

import { describe, it, expect } from 'vitest'
import { sanitizeCsvCell, sanitizeCsvRow, rowsToCsv } from '../csv'

describe('CSV Formula Injection Prevention', () => {
  describe('sanitizeCsvCell', () => {
    it('escapes formula with leading equals sign', () => {
      expect(sanitizeCsvCell('=SUM(A1:A10)')).toBe("'=SUM(A1:A10)")
      expect(sanitizeCsvCell('=1+1')).toBe("'=1+1")
      expect(sanitizeCsvCell('=cmd|"/c calc"')).toBe('\'=cmd|"/c calc"')
    })

    it('escapes formula with leading plus sign', () => {
      expect(sanitizeCsvCell('+1234567890')).toBe("'+1234567890")
      expect(sanitizeCsvCell('+SUM(A1:A10)')).toBe("'+SUM(A1:A10)")
    })

    it('escapes formula with leading minus sign', () => {
      expect(sanitizeCsvCell('-1234567890')).toBe("'-1234567890")
      expect(sanitizeCsvCell('-SUM(A1:A10)')).toBe("'-SUM(A1:A10)")
    })

    it('escapes formula with leading @ sign', () => {
      expect(sanitizeCsvCell('@SUM(A1:A10)')).toBe("'@SUM(A1:A10)")
    })

    it('escapes formula with leading pipe', () => {
      expect(sanitizeCsvCell('|cmd')).toBe("'|cmd")
    })

    it('escapes formula with leading tab', () => {
      expect(sanitizeCsvCell('\t=SUM(A1)')).toBe("'\t=SUM(A1)")
    })

    it('escapes double quotes in values', () => {
      expect(sanitizeCsvCell('Title "with quotes"')).toBe('Title ""with quotes""')
      expect(sanitizeCsvCell('="test"')).toBe('\'=""test""')
    })

    it('leaves safe values unchanged (except quote escaping)', () => {
      expect(sanitizeCsvCell('Normal title')).toBe('Normal title')
      expect(sanitizeCsvCell('Title: Research')).toBe('Title: Research')
      expect(sanitizeCsvCell('123')).toBe('123')
      expect(sanitizeCsvCell('2024-11-06')).toBe('2024-11-06')
    })

    it('handles empty and null values', () => {
      expect(sanitizeCsvCell('')).toBe('')
      expect(sanitizeCsvCell(null)).toBe('')
      expect(sanitizeCsvCell(undefined)).toBe('')
    })

    it('handles numbers', () => {
      expect(sanitizeCsvCell(123)).toBe('123')
      expect(sanitizeCsvCell(0)).toBe('0')
      expect(sanitizeCsvCell(-456)).toBe('-456')  // Negative number becomes string
    })
  })

  describe('sanitizeCsvRow', () => {
    it('sanitizes entire row', () => {
      const row = ['Normal', '=FORMULA', 123, null, '+123']
      const result = sanitizeCsvRow(row)
      
      expect(result).toEqual([
        'Normal',
        "'=FORMULA",
        '123',
        '',
        "'+123"
      ])
    })
  })

  describe('rowsToCsv', () => {
    it('creates safe CSV with headers', () => {
      const headers = ['ID', 'Title', 'Value']
      const rows = [
        [1, 'Normal Title', 100],
        [2, '=EVIL()', 200],
        [3, 'Title "quoted"', 300]
      ]
      
      const csv = rowsToCsv(headers, rows)
      const lines = csv.split('\n')
      
      // Check header
      expect(lines[0]).toBe('"ID","Title","Value"')
      
      // Check safe row
      expect(lines[1]).toBe('"1","Normal Title","100"')
      
      // Check formula escaped
      expect(lines[2]).toContain("'=EVIL()")
      
      // Check quotes escaped
      expect(lines[3]).toContain('Title ""quoted""')
    })
  })
})

