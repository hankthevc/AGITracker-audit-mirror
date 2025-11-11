import { test, expect } from '@playwright/test'

test.describe('OpenGraph Images', () => {
  test('should return OG image with correct content-type', async ({ request }) => {
    const response = await request.get('/api/og?title=Test&description=Test Description')
    
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('image')
  })

  test('should generate image with custom title and description', async ({ request }) => {
    const title = encodeURIComponent('AGI Signpost Tracker')
    const description = encodeURIComponent('Evidence-first dashboard')
    
    const response = await request.get(`/api/og?title=${title}&description=${description}`)
    
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('image')
    
    // Verify image size is reasonable (should be > 1KB for a 1200x630 image)
    const buffer = await response.body()
    expect(buffer.length).toBeGreaterThan(1000)
  })

  test('should handle missing parameters gracefully', async ({ request }) => {
    const response = await request.get('/api/og')
    
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('image')
  })
})

