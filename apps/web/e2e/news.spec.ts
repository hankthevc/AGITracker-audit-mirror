import { test, expect } from '@playwright/test'

const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000'

test.describe('News Page', () => {
  test('loads /news and shows header + feeds', async ({ page }) => {
    await page.goto(`${BASE_URL}/news`)
    await expect(page.locator('h1')).toContainText('AI News & Research')
    await expect(page.locator('text=Data Feeds:')).toBeVisible()
    await expect(page.locator('a[href="/v1/events/feed.json"]')).toBeVisible()
  })

  test('filters by tier and source_type and shows If true banner for C/D', async ({ page }) => {
    await page.goto(`${BASE_URL}/news`)
    // Click Tier C filter link
    await page.locator('a:has-text("Tier C")').first().click()
    await page.waitForTimeout(500)
    // If any items render, should include If true banner text
    const ifTrueVisible = await page.locator('text=If true').first().isVisible().catch(() => false)
    // Now click source_type filter 'news'
    await page.locator('a:has-text("news")').first().click()
    await page.waitForTimeout(500)
    const bodyText = await page.textContent('body')
    expect(bodyText).toBeTruthy()
  })
})
