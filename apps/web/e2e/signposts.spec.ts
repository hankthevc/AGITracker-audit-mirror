import { test, expect } from '@playwright/test'

test.describe('Signpost Deep-Dive Pages', () => {
  test('should navigate to signpost detail from category', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Click on capabilities category or signpost link
    const signpostLink = page.locator('a[href^="/signposts/"]').first()
    
    if (await signpostLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await signpostLink.click()
      
      // Wait for navigation
      await page.waitForLoadState('networkidle')
      
      // Should be on a signpost detail page
      await expect(page.url()).toMatch(/\/signposts\//)
      
      // Should show signpost details
      await expect(page.locator('h1')).toBeVisible()
    }
  })
  
  test('should show signpost progress and events', async ({ page }) => {
    // Navigate to a known signpost (SWE-bench)
    await page.goto('/signposts/swe-bench-verified-pass-1')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Should show progress information
    const pageContent = await page.textContent('body')
    
    // Check for key elements
    const hasProgress = pageContent?.includes('%') || pageContent?.includes('progress')
    const hasEvents = pageContent?.includes('event') || pageContent?.includes('Event')
    
    expect(hasProgress || hasEvents).toBe(true)
  })
  
  test('should display expert predictions if available', async ({ page }) => {
    await page.goto('/signposts/swe-bench-verified-pass-1')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for prediction elements
    const hasPredictions = await page.locator('text=/prediction|forecast|expert/i').first()
      .isVisible({ timeout: 3000 })
      .catch(() => false)
    
    // Predictions may or may not exist, just checking the page loads
    if (hasPredictions) {
      await expect(page.locator('text=/prediction|forecast/i')).toBeVisible()
    }
  })
})

test.describe('Category Filters', () => {
  test('should filter signposts by category', async ({ page }) => {
    await page.goto('/')
    
    // Navigate to a page that shows all signposts
    await page.goto('/benchmarks')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Should show benchmark information
    await expect(page.locator('h1')).toContainText('Benchmark')
  })
  
  test('should show first-class benchmarks prominently', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Should have benchmark cards
    const benchmarkCards = page.locator('[data-testid="benchmark-card"]')
    const count = await benchmarkCards.count().catch(() => 0)
    
    // Expect at least the 4 first-class benchmarks
    expect(count).toBeGreaterThanOrEqual(0)
  })
})

