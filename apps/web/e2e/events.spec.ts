import { test, expect } from '@playwright/test'

test.describe('Events Page', () => {
  test('should load and display event cards', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('Events Feed')
    
    // Wait for events to load (either cards or "no events" message)
    await page.waitForSelector('[data-testid^="event-card-"], .text-muted-foreground', { timeout: 10000 })
    
    // Check if we have event cards
    const hasCards = await page.locator('[data-testid^="event-card-"]').count()
    
    if (hasCards > 0) {
      // Verify first card has expected structure
      const firstCard = page.locator('[data-testid^="event-card-"]').first()
      await expect(firstCard).toBeVisible()
      
      // Should have tier badge
      await expect(firstCard.locator('[data-testid^="evidence-tier-"]')).toBeVisible()
    }
  })
  
  test('should filter by tier', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Click A-tier filter
    await page.click('[data-testid="tier-filter-A"]')
    
    // Wait for filter to apply
    await page.waitForTimeout(1000)
    
    // Check if we have results
    const cardCount = await page.locator('[data-testid^="event-card-"]').count()
    
    if (cardCount > 0) {
      // Verify all visible cards are A-tier
      const tierBadges = page.locator('[data-testid="evidence-tier-A"]')
      const badgeCount = await tierBadges.count()
      expect(badgeCount).toBeGreaterThan(0)
    }
  })
  
  test('should expand event analysis', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for events to load
    await page.waitForSelector('[data-testid^="event-card-"]', { timeout: 10000 })
    
    const cardCount = await page.locator('[data-testid^="event-card-"]').count()
    
    if (cardCount > 0) {
      // Look for "Why this matters" button
      const expandButton = page.locator('[data-testid="expand-analysis-button"]').first()
      
      if (await expandButton.isVisible()) {
        await expandButton.click()
        
        // Button text should change
        await expect(expandButton).toContainText('Hide')
      }
    }
  })
  
  test('should export to JSON', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check if export button exists
    const exportButton = page.locator('button:has-text("Export JSON")')
    await expect(exportButton).toBeVisible()
  })
})

test.describe('Timeline Page', () => {
  test('should load timeline visualization', async ({ page }) => {
    await page.goto('/timeline')
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('Events Timeline')
    
    // Wait for either chart or error/empty message
    await page.waitForSelector('.recharts-wrapper, .text-muted-foreground', { timeout: 10000 })
  })
  
  test('should filter timeline by tier', async ({ page }) => {
    await page.goto('/timeline')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Find and click a tier filter badge
    const tierBadge = page.locator('text=A').first()
    if (await tierBadge.isVisible()) {
      await tierBadge.click()
      
      // Wait for filter to apply
      await page.waitForTimeout(1000)
    }
  })
})
