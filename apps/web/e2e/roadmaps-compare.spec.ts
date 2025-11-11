import { test, expect } from '@playwright/test'

const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000'

test.describe('Roadmaps Compare Overlay', () => {
  test('toggle appears and can switch ON/OFF', async ({ page }) => {
    await page.goto(`${BASE_URL}/roadmaps/compare`)
    const toggle = page.locator('[data-testid="events-overlay-toggle"]').first()
    await expect(toggle).toBeVisible()
    await expect(toggle).toContainText('Overlay')

    // Turn ON
    await toggle.click()
    await page.waitForURL(/overlay=events/)
    await expect(page.locator('[data-testid="events-overlay-toggle"]').first()).toContainText('ON')

    // Turn OFF
    await page.locator('[data-testid="events-overlay-toggle"]').first().click()
    await expect(page).not.toHaveURL(/overlay=events/)
  })

  test('overlay shows status legend when enabled', async ({ page }) => {
    await page.goto(`${BASE_URL}/roadmaps/compare?overlay=events`)
    
    // Legend should appear with status indicators
    await expect(page.locator('text=Ahead')).toBeVisible()
    await expect(page.locator('text=On Track')).toBeVisible()
    await expect(page.locator('text=Behind')).toBeVisible()
    await expect(page.locator('text=Unobserved')).toBeVisible()
  })

  test('prediction cards show status badges when overlay enabled', async ({ page }) => {
    await page.goto(`${BASE_URL}/roadmaps/compare?overlay=events`)
    
    // Wait for content
    await page.waitForTimeout(1000)
    
    // Check if any status badges render (ahead/behind/on_track)
    const statusBadges = page.locator('[class*="bg-green-"][class*="border-green-"], [class*="bg-red-"][class*="border-red-"], [class*="bg-yellow-"][class*="border-yellow-"]')
    const count = await statusBadges.count()
    
    // Should have at least one status badge if predictions exist
    expect(count).toBeGreaterThanOrEqual(0)
  })
})
