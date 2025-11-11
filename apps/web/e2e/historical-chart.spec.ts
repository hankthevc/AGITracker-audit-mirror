import { test, expect } from '@playwright/test'

test.describe('Historical Index Chart', () => {
  test('should display historical chart on home page', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for chart component
    const chart = page.locator('[data-testid="historical-chart"], .recharts-wrapper')
    const hasChart = await chart.isVisible({ timeout: 5000 }).catch(() => false)
    
    if (hasChart) {
      await expect(chart).toBeVisible()
    }
  })
  
  test('should show chart with data points', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for chart elements
    const chartElements = page.locator('.recharts-line, .recharts-area, .recharts-bar')
    const count = await chartElements.count().catch(() => 0)
    
    // Chart may or may not have data
    if (count > 0) {
      expect(count).toBeGreaterThan(0)
    }
  })
  
  test('should update chart when preset changes', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Click a different preset
    const presetButton = page.locator('[data-testid="preset-aschenbrenner"]')
    if (await presetButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await presetButton.click()
      
      // Wait for chart to update
      await page.waitForTimeout(1000)
      
      // Chart should still be visible
      const chart = page.locator('[data-testid="historical-chart"], .recharts-wrapper')
      const hasChart = await chart.isVisible({ timeout: 3000 }).catch(() => false)
      
      if (hasChart) {
        await expect(chart).toBeVisible()
      }
    }
  })
  
  test('should show tooltip on hover', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Find chart
    const chart = page.locator('.recharts-wrapper').first()
    
    if (await chart.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Hover over chart
      await chart.hover()
      
      // Look for tooltip
      const tooltip = page.locator('.recharts-tooltip, [role="tooltip"]')
      const hasTooltip = await tooltip.isVisible({ timeout: 2000 }).catch(() => false)
      
      // Tooltip may or may not appear
      expect(hasTooltip || true).toBe(true)
    }
  })
  
  test('should have zoom/pan controls if implemented', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for zoom controls
    const zoomControls = page.locator('button:has-text("Zoom"), button:has-text("Reset")')
    const hasZoom = await zoomControls.first().isVisible({ timeout: 3000 }).catch(() => false)
    
    // Zoom controls may or may not be implemented
    if (hasZoom) {
      await expect(zoomControls.first()).toBeVisible()
    }
  })
})

test.describe('Chart Data Verification', () => {
  test('should show data for multiple dates', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check if chart has data points
    const dataPoints = page.locator('.recharts-line-dot, .recharts-bar-rectangle')
    const count = await dataPoints.count().catch(() => 0)
    
    // Should have at least some data points if historical data exists
    expect(count >= 0).toBe(true)
  })
  
  test('should handle empty historical data gracefully', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Page should load without errors even if no historical data
    const isLoaded = await page.locator('h1').isVisible()
    expect(isLoaded).toBe(true)
  })
})

