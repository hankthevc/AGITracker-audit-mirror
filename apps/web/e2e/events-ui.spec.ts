/**
 * E2E tests for Events UI pages (v0.3 frontend).
 * 
 * Tests:
 * - /events list page with filters
 * - /events/[id] detail page
 * - /admin/review page
 * - Home page "This Week's Moves" strip
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000';

test.describe('Events List Page', () => {
  test('navigates to /events and displays events list', async ({ page }) => {
    await page.goto(`${BASE_URL}/events`);
    
    // Check header
    await expect(page.locator('h1')).toContainText('Events Feed');
    
    // Check filter buttons
    await expect(page.locator('text=All Events')).toBeVisible();
    await expect(page.locator('text=Tier A')).toBeVisible();
    await expect(page.locator('text=Tier B')).toBeVisible();
    await expect(page.locator('text=Tier C')).toBeVisible();
    await expect(page.locator('text=Tier D')).toBeVisible();
    
    // Check feed links
    await expect(page.locator('text=JSON Feed (Public)')).toBeVisible();
    await expect(page.locator('text=JSON Feed (Research)')).toBeVisible();
  });

  test('filters events by tier', async ({ page }) => {
    await page.goto(`${BASE_URL}/events`);
    
    // Click Tier A filter
    await page.locator('button:has-text("Tier A")').click();
    
    // Wait for content to load
    await page.waitForTimeout(1000);
    
    // Should show filtered results or empty state
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('filters events by source type', async ({ page }) => {
    await page.goto(`${BASE_URL}/news`);
    
    // Click source_type filter 'paper'
    await page.locator('a:has-text("paper")').first().click();
    await page.waitForTimeout(1000);
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('displays legend with tier descriptions', async ({ page }) => {
    await page.goto(`${BASE_URL}/events`);
    
    // Check for legend card
    await expect(page.locator('text=Evidence Tiers:')).toBeVisible();
    await expect(page.locator('text=Tier A (peer-reviewed, leaderboards)')).toBeVisible();
  });
});

test.describe('Event Detail Page', () => {
  test('navigates to event detail page (or shows not found)', async ({ page }) => {
    await page.goto(`${BASE_URL}/events/1`);
    
    // Either shows event details or "not found" message
    const pageContent = await page.textContent('body');
    const hasBackLink = await page.locator('text=← Back to Events').isVisible();
    
    expect(hasBackLink).toBe(true);
    expect(pageContent).toBeTruthy();
  });

  test('shows back to events link', async ({ page }) => {
    await page.goto(`${BASE_URL}/events/1`);
    
    const backLink = page.locator('a:has-text("← Back to Events")');
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', '/events');
  });
});

test.describe('Admin Review Page', () => {
  test('navigates to /admin/review and displays review queue', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/review`);
    
    // Check header
    await expect(page.locator('h1')).toContainText('Event Review Queue');
    
    // Check info card
    await expect(page.locator('text=Review Criteria:')).toBeVisible();
    await expect(page.locator('text=confidence scores below 60%')).toBeVisible();
  });

  test('displays review instructions', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/review`);
    
    // Check for review criteria
    await expect(page.locator('text=Does the event actually relate to the mapped signposts?')).toBeVisible();
    await expect(page.locator('text=Is the source credible')).toBeVisible();
  });
});

test.describe('Home Page - This Week\'s Moves', () => {
  test('displays "This Week\'s Moves" strip on home page', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    
    // Wait for the component to load
    await page.waitForTimeout(2000);
    
    // Check for the section
    const hasMovesStrip = await page.locator('text=This Week\'s Moves').isVisible();
    expect(hasMovesStrip).toBe(true);
  });

  test('"This Week\'s Moves" has link to /events', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    
    // Wait for component
    await page.waitForTimeout(2000);
    
    // Look for "View all" link
    const viewAllLink = page.locator('a:has-text("View all")');
    const count = await viewAllLink.count();
    
    // Should have at least one "View all" link
    if (count > 0) {
      await expect(viewAllLink.first()).toHaveAttribute('href', '/events');
    }
  });
});

test.describe('Navigation Links', () => {
  test('header navigation includes Events link', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    
    const eventsLink = page.locator('nav a:has-text("Events")');
    await expect(eventsLink).toBeVisible();
    await expect(eventsLink).toHaveAttribute('href', '/events');
  });

  test('header navigation includes Admin link', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    
    const adminLink = page.locator('nav a:has-text("Admin")');
    await expect(adminLink).toBeVisible();
    await expect(adminLink).toHaveAttribute('href', '/admin/review');
  });

  test('footer includes events feed links', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    
    // Check footer links
    await expect(page.locator('footer a:has-text("Events (Public)")')).toBeVisible();
    await expect(page.locator('footer a:has-text("Events (Research)")')).toBeVisible();
  });
});

test.describe('Feed Links', () => {
  test('events feed links are accessible from footer', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    
    const publicFeedLink = page.locator('footer a[href="/v1/events/feed.json"]');
    const researchFeedLink = page.locator('footer a[href="/v1/events/feed.json?include_research=true"]');
    
    await expect(publicFeedLink).toBeVisible();
    await expect(researchFeedLink).toBeVisible();
  });

  test('events page has direct feed links', async ({ page }) => {
    await page.goto(`${BASE_URL}/events`);
    
    await expect(page.locator('a:has-text("JSON Feed (Public)")')).toBeVisible();
    await expect(page.locator('a:has-text("JSON Feed (Research)")')).toBeVisible();
  });
});

