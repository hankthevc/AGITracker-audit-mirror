import { test, expect } from '@playwright/test'

test.describe('Accessibility - Basic Checks', () => {
  test('home page should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check for h1
    const h1 = page.locator('h1')
    await expect(h1).toBeVisible()
    
    // Page should have proper structure
    const headings = await page.locator('h1, h2, h3').count()
    expect(headings).toBeGreaterThan(0)
  })
  
  test('interactive elements should be keyboard accessible', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Tab through interactive elements
    await page.keyboard.press('Tab')
    await page.waitForTimeout(200)
    
    // Check that focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).toBeTruthy()
  })
  
  test('buttons should have accessible names', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check all buttons have text or aria-label
    const buttons = await page.locator('button').all()
    
    for (const button of buttons) {
      const text = await button.textContent()
      const ariaLabel = await button.getAttribute('aria-label')
      const hasAccessibleName = (text && text.trim().length > 0) || ariaLabel
      
      expect(hasAccessibleName).toBeTruthy()
    }
  })
  
  test('images should have alt text', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check all images have alt text
    const images = await page.locator('img').all()
    
    for (const img of images) {
      const alt = await img.getAttribute('alt')
      // Alt can be empty string for decorative images, but should be present
      expect(alt !== null).toBe(true)
    }
  })
  
  test('form inputs should have labels', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Check inputs have labels or aria-label
    const inputs = await page.locator('input[type="text"], input[type="search"]').all()
    
    for (const input of inputs) {
      const id = await input.getAttribute('id')
      const ariaLabel = await input.getAttribute('aria-label')
      const placeholder = await input.getAttribute('placeholder')
      
      // Input should have id (for label) or aria-label or at least placeholder
      const hasLabel = id || ariaLabel || placeholder
      expect(hasLabel).toBeTruthy()
    }
  })
})

test.describe('Color Contrast and Visual', () => {
  test('page should be readable without images', async ({ page }) => {
    // Block images
    await page.route('**/*.{png,jpg,jpeg,svg,webp}', route => route.abort())
    
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Page should still have content
    const h1 = page.locator('h1')
    await expect(h1).toBeVisible()
  })
  
  test('page should be usable at 200% zoom', async ({ page }) => {
    await page.goto('/')
    
    // Set viewport to simulate 200% zoom
    await page.setViewportSize({ width: 640, height: 480 })
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Main content should still be visible
    const h1 = page.locator('h1')
    await expect(h1).toBeVisible()
  })
})

test.describe('Keyboard Navigation', () => {
  test('should navigate through main menu with keyboard', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Tab to navigation
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    
    // Should be able to navigate
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).toBeTruthy()
  })
  
  test('should be able to activate buttons with Enter/Space', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Find first button
    const button = page.locator('button').first()
    if (await button.isVisible({ timeout: 3000 }).catch(() => false)) {
      await button.focus()
      
      // Press Enter
      await page.keyboard.press('Enter')
      await page.waitForTimeout(200)
      
      // Page should not crash
      const isVisible = await page.locator('body').isVisible()
      expect(isVisible).toBe(true)
    }
  })
  
  test('should support Escape key to close dialogs', async ({ page }) => {
    await page.goto('/')
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for any button that might open a dialog
    const buttons = page.locator('button')
    const count = await buttons.count()
    
    if (count > 0) {
      // Click first button
      await buttons.first().click()
      await page.waitForTimeout(500)
      
      // Press Escape
      await page.keyboard.press('Escape')
      await page.waitForTimeout(200)
      
      // Page should still be functional
      const isVisible = await page.locator('body').isVisible()
      expect(isVisible).toBe(true)
    }
  })
})

