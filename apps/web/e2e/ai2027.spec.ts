import { test, expect } from '@playwright/test'

test.describe('AI-2027 Roadmap Page', () => {
  test('loads timeline with predictions', async ({ page }) => {
    await page.goto('/roadmaps/ai-2027')
    
    // Check page title
    await expect(page.locator('h1')).toContainText('AI 2027')
    
    // Timeline items should be present
    const timelineItems = await page.locator('[data-testid^="timeline-item-"]').count()
    expect(timelineItems).toBeGreaterThan(0)
  })

  test('displays status badges', async ({ page }) => {
    await page.goto('/roadmaps/ai-2027')
    
    // Check for status badges (ahead/on_track/behind)
    const aheadBadges = await page.locator('[data-testid="status-ahead"]').count()
    const onTrackBadges = await page.locator('[data-testid="status-on_track"]').count()
    const behindBadges = await page.locator('[data-testid="status-behind"]').count()
    
    // At least one status badge should be present
    const totalBadges = aheadBadges + onTrackBadges + behindBadges
    expect(totalBadges).toBeGreaterThan(0)
  })

  test('timeline items are clickable', async ({ page }) => {
    await page.goto('/roadmaps/ai-2027')
    
    // Get first timeline item
    const firstItem = page.locator('[data-testid^="timeline-item-"]').first()
    await expect(firstItem).toBeVisible()
    
    // Click should open evidence modal
    const card = firstItem.locator('div[class*="cursor-pointer"]').first()
    await card.click()
    
    // Modal should appear (checking for modal content)
    await expect(page.getByText(/Prediction|Target|Confidence/i)).toBeVisible()
  })

  test('shows preset weights', async ({ page }) => {
    await page.goto('/roadmaps/ai-2027')
    
    // Preset weights card should show category percentages
    await expect(page.getByText(/35%|30%|25%|10%/)).toBeVisible()
    await expect(page.getByText(/Agents|Capabilities|Inputs|Security/i)).toBeVisible()
  })

  test('displays scenario overview', async ({ page }) => {
    await page.goto('/roadmaps/ai-2027')
    
    // Scenario overview should be present
    await expect(page.getByText('Scenario Overview')).toBeVisible()
    await expect(page.getByText(/2027|AGI|autonomous/i)).toBeVisible()
  })

  test('shows status indicators legend', async ({ page }) => {
    await page.goto('/roadmaps/ai-2027')
    
    // Status indicators explanation should be present
    await expect(page.getByText('Status Indicators')).toBeVisible()
    await expect(page.getByText(/Ahead|On|Behind/i)).toBeVisible()
  })
})

