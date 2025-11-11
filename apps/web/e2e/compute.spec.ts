import { test, expect } from '@playwright/test'

test.describe('Compute Page', () => {
  test('loads and displays OOM meters', async ({ page }) => {
    await page.goto('/compute')
    
    // Check page title
    await expect(page.locator('h1')).toContainText('Compute')
    
    // OOMMeter should be present
    await expect(page.locator('[data-testid="oom-meter"]')).toBeVisible()
    
    // Multiple OOM meters (FLOPs, DC Power, Algo Efficiency)
    const oomMeters = await page.locator('[data-testid="oom-meter"]').count()
    expect(oomMeters).toBeGreaterThan(0)
  })

  test('displays training compute milestones', async ({ page }) => {
    await page.goto('/compute')
    
    // Should show FLOPs milestones
    await expect(page.getByText(/1e25|1e26|1e27/)).toBeVisible()
    await expect(page.getByText(/FLOP/i)).toBeVisible()
  })

  test('displays DC power milestones', async ({ page }) => {
    await page.goto('/compute')
    
    // Should show DC power milestones
    await expect(page.getByText(/GW|Gigawatt/i)).toBeVisible()
    await expect(page.getByText(/Data Center|DC/i)).toBeVisible()
  })

  test('displays algorithmic efficiency', async ({ page }) => {
    await page.goto('/compute')
    
    // Should show algo efficiency
    await expect(page.getByText(/Algorithmic Efficiency|Algorithm/i)).toBeVisible()
    await expect(page.getByText(/OOM|magnitude/i)).toBeVisible()
  })

  test('shows methodology explanation', async ({ page }) => {
    await page.goto('/compute')
    
    // Methodology card should be present
    await expect(page.getByText('Methodology')).toBeVisible()
  })
})

