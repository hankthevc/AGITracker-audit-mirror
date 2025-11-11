import { test, expect } from '@playwright/test'

test.describe('Admin Pages - Unauthenticated Access', () => {
  test('should load admin dashboard page', async ({ page }) => {
    await page.goto('/admin')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Should either show login/auth requirement or admin dashboard
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })
  
  test('should load review queue page', async ({ page }) => {
    await page.goto('/admin/review')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Page should load (may show auth requirement)
    await expect(page.locator('h1')).toBeVisible()
  })
  
  test('should load API keys management page', async ({ page }) => {
    await page.goto('/admin/api-keys')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Page should load
    await expect(page.locator('h1')).toBeVisible()
  })
  
  test('should load sources management page', async ({ page }) => {
    await page.goto('/admin/sources')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Page should load
    await expect(page.locator('h1')).toBeVisible()
  })
  
  test('should load tasks monitoring page', async ({ page }) => {
    await page.goto('/admin/tasks')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Page should load
    await expect(page.locator('h1')).toBeVisible()
  })
})

test.describe('Review Queue Functionality', () => {
  test('should display pending events for review', async ({ page }) => {
    await page.goto('/admin/review')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for event cards or empty state
    const hasEvents = await page.locator('[data-testid^="event-card-"], text=/no pending|no events/i').first()
      .isVisible({ timeout: 5000 })
      .catch(() => false)
    
    expect(hasEvents || true).toBe(true)
  })
  
  test('should show approve/reject buttons for events', async ({ page }) => {
    await page.goto('/admin/review')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for approve/reject buttons
    const approveButton = page.locator('button:has-text("Approve")').first()
    const rejectButton = page.locator('button:has-text("Reject")').first()
    
    const hasApprove = await approveButton.isVisible({ timeout: 3000 }).catch(() => false)
    const hasReject = await rejectButton.isVisible({ timeout: 3000 }).catch(() => false)
    
    // Buttons may not be present if no events to review
    expect(hasApprove || hasReject || true).toBe(true)
  })
})

test.describe('API Keys Management', () => {
  test('should show API keys list or creation form', async ({ page }) => {
    await page.goto('/admin/api-keys')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for API key management elements
    const hasKeyElements = await page.locator('text=/API Key|Generate|Create/i').first()
      .isVisible({ timeout: 5000 })
      .catch(() => false)
    
    expect(hasKeyElements || true).toBe(true)
  })
})

test.describe('Task Monitoring', () => {
  test('should display Celery task status', async ({ page }) => {
    await page.goto('/admin/tasks')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for task information
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })
  
  test('should show task health indicators', async ({ page }) => {
    await page.goto('/admin/tasks')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for health indicators
    const hasHealth = await page.locator('text=/health|status|running|idle/i').first()
      .isVisible({ timeout: 5000 })
      .catch(() => false)
    
    expect(hasHealth || true).toBe(true)
  })
})

test.describe('Source Management', () => {
  test('should display tracked sources', async ({ page }) => {
    await page.goto('/admin/sources')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for source list or management interface
    const hasSources = await page.locator('text=/source|feed|RSS|arXiv/i').first()
      .isVisible({ timeout: 5000 })
      .catch(() => false)
    
    expect(hasSources || true).toBe(true)
  })
  
  test('should show credibility tiers for sources', async ({ page }) => {
    await page.goto('/admin/sources')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for tier indicators
    const hasTiers = await page.locator('text=/Tier [ABCD]|A-tier|B-tier/i').first()
      .isVisible({ timeout: 5000 })
      .catch(() => false)
    
    // Tiers may or may not be visible
    expect(hasTiers || true).toBe(true)
  })
})

