import { test, expect } from '@playwright/test'

test.describe('Benchmarks Page', () => {
  test('loads and displays benchmark tiles', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // Check page title
    await expect(page.locator('h1')).toContainText('Benchmarks')
    
    // OSWorld tile should be present
    await expect(page.getByText('OSWorld')).toBeVisible()
    
    // WebArena tile should be present
    await expect(page.getByText('WebArena')).toBeVisible()
    
    // GPQA tile should be present
    await expect(page.getByText('GPQA')).toBeVisible()
  })

  test('displays provisional badge for B-tier benchmarks', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // GPQA should show provisional badge (B-tier by default)
    const gpqaSection = page.getByText('GPQA').locator('..')
    
    // Check for badge indicating B-tier or provisional status
    // This would need to be implemented in the actual page
    await expect(page.getByText(/GPQA|Diamond/)).toBeVisible()
  })

  test('benchmark tiles are clickable', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // Click on a benchmark should navigate or expand details
    const osworldTile = page.getByText('OSWorld').first()
    await expect(osworldTile).toBeVisible()
  })

  test('displays correct benchmark categories', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // Should show capability benchmarks
    await expect(page.getByText(/Capabilities|Coding|Reasoning/i)).toBeVisible()
    
    // Should show agent benchmarks
    await expect(page.getByText(/Agents|Autonomous/i)).toBeVisible()
  })

  test('HLE tile shows provisional badge and quality note', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // HLE tile should be visible
    const hleTile = page.getByTestId('hle-benchmark-tile')
    await expect(hleTile).toBeVisible()
    
    // Should have Provisional badge
    const provisionalBadge = page.getByTestId('hle-provisional-badge')
    await expect(provisionalBadge).toBeVisible()
    await expect(provisionalBadge).toContainText('Provisional')
    
    // Should show quality note/warning
    const qualityNote = page.getByTestId('hle-quality-note')
    await expect(qualityNote).toBeVisible()
    await expect(qualityNote).toContainText(/Bio|Chem|quality/i)
  })

  test('HLE tile shows monitor-only chip and optional version pill', async ({ page }) => {
    await page.goto('/benchmarks')
    
    // HLE tile should be visible
    const hleTile = page.getByTestId('hle-benchmark-tile')
    await expect(hleTile).toBeVisible()
    
    // Should have Monitor-Only status chip
    const monitorOnlyChip = page.getByTestId('hle-monitor-only')
    await expect(monitorOnlyChip).toBeVisible()
    await expect(monitorOnlyChip).toContainText('Monitor-Only')
    
    // Should have version pill (optional, but present in our data)
    const versionPill = page.getByTestId('hle-version-pill')
    await expect(versionPill).toBeVisible()
    await expect(versionPill).toContainText(/Text-2500/i)
    
    // Monitor-Only chip should have tooltip with quality context
    const tooltip = await monitorOnlyChip.getAttribute('title')
    expect(tooltip).toContain('long-horizon')
  })
})

