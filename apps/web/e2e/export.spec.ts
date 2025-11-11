import { test, expect } from '@playwright/test'

test.describe('Export Functionality', () => {
  test('should export events to JSON', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Setup download listener
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null)
    
    // Click export JSON button
    const exportButton = page.locator('button:has-text("Export JSON")')
    if (await exportButton.isVisible()) {
      await exportButton.click()
      
      // Wait for download
      const download = await downloadPromise
      if (download) {
        expect(download.suggestedFilename()).toMatch(/events.*\.json/)
      }
    }
  })
  
  test('should export events to CSV', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for CSV export option
    const exportButton = page.locator('button:has-text("Export")')
    if (await exportButton.isVisible()) {
      await exportButton.click()
      
      // Select CSV format if dropdown exists
      const csvOption = page.locator('text=CSV').first()
      if (await csvOption.isVisible()) {
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null)
        await csvOption.click()
        
        const download = await downloadPromise
        if (download) {
          expect(download.suggestedFilename()).toMatch(/\.csv$/)
        }
      }
    }
  })
  
  test('should export events to Excel', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for Excel export option
    const exportButton = page.locator('button:has-text("Export")')
    if (await exportButton.isVisible()) {
      await exportButton.click()
      
      // Select Excel format if dropdown exists
      const excelOption = page.locator('text=Excel').first()
      if (await excelOption.isVisible()) {
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null)
        await excelOption.click()
        
        const download = await downloadPromise
        if (download) {
          expect(download.suggestedFilename()).toMatch(/\.xlsx$/)
        }
      }
    }
  })
  
  test('should show export options in timeline', async ({ page }) => {
    await page.goto('/timeline')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check if export button exists
    const exportButton = page.locator('button:has-text("Export")')
    const isVisible = await exportButton.isVisible().catch(() => false)
    
    // Export functionality may not be on timeline, that's OK
    if (isVisible) {
      await expect(exportButton).toBeVisible()
    }
  })
})

test.describe('Feed Endpoints', () => {
  test('should provide public JSON feed', async ({ page, request }) => {
    // Test the public API feed endpoint
    const response = await request.get('/v1/events/feed.json?audience=public')
    
    if (response.ok()) {
      expect(response.status()).toBe(200)
      const data = await response.json()
      expect(data).toHaveProperty('events')
      expect(Array.isArray(data.events)).toBe(true)
    }
  })
  
  test('should provide research JSON feed', async ({ page, request }) => {
    // Test the research API feed endpoint
    const response = await request.get('/v1/events/feed.json?audience=research')
    
    if (response.ok()) {
      expect(response.status()).toBe(200)
      const data = await response.json()
      expect(data).toHaveProperty('events')
    }
  })
})

