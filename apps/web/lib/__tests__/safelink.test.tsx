/**
 * SafeLink Security Tests - BLOCKING in CI
 * 
 * Tests that SafeLink component properly prevents XSS attacks via
 * dangerous URL schemes (javascript:, data:, vbscript:).
 */

import { render, screen } from "@testing-library/react"
import { SafeLink } from "../SafeLink"

describe("SafeLink Security", () => {
  it("blocks javascript: URLs and renders as plain text", () => {
    const { container } = render(
      <SafeLink href="javascript:alert('XSS')">Malicious Link</SafeLink>
    )
    
    // Should NOT render an anchor tag
    expect(container.querySelector("a")).toBeNull()
    
    // Should render as plain text with warning title
    const span = container.querySelector("span")
    expect(span).toBeInTheDocument()
    expect(span).toHaveTextContent("Malicious Link")
    expect(span).toHaveAttribute("title", expect.stringContaining("Blocked unsafe URL"))
  })

  it("blocks data: URLs", () => {
    const { container } = render(
      <SafeLink href="data:text/html,<script>alert('XSS')</script>">Data URL</SafeLink>
    )
    
    expect(container.querySelector("a")).toBeNull()
    expect(container.querySelector("span")).toBeInTheDocument()
  })

  it("blocks vbscript: URLs", () => {
    const { container } = render(
      <SafeLink href="vbscript:msgbox('XSS')">VBScript URL</SafeLink>
    )
    
    expect(container.querySelector("a")).toBeNull()
    expect(container.querySelector("span")).toBeInTheDocument()
  })

  it("allows https: URLs", () => {
    render(<SafeLink href="https://example.com">Safe Link</SafeLink>)
    
    const link = screen.getByText("Safe Link").closest("a")
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute("href", "https://example.com")
  })

  it("allows http: URLs", () => {
    render(<SafeLink href="http://example.com">HTTP Link</SafeLink>)
    
    const link = screen.getByText("HTTP Link").closest("a")
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute("href", "http://example.com")
  })

  it("allows mailto: URLs", () => {
    render(<SafeLink href="mailto:test@example.com">Email</SafeLink>)
    
    const link = screen.getByText("Email").closest("a")
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute("href", "mailto:test@example.com")
  })

  it("enforces rel='noopener noreferrer' for external links", () => {
    render(<SafeLink href="https://external.com">External</SafeLink>)
    
    const link = screen.getByText("External").closest("a")
    expect(link).toHaveAttribute("rel", "noopener noreferrer")
  })

  it("handles invalid URLs gracefully", () => {
    const { container } = render(
      <SafeLink href="not a valid url">Invalid</SafeLink>
    )
    
    // Should render as plain text, not throw error
    expect(container.querySelector("span")).toBeInTheDocument()
    expect(container.querySelector("a")).toBeNull()
  })

  it("handles missing href gracefully", () => {
    const { container } = render(
      <SafeLink>No HREF</SafeLink>
    )
    
    expect(container.querySelector("span")).toBeInTheDocument()
    expect(container.querySelector("a")).toBeNull()
  })

  it("preserves className and other props for safe links", () => {
    render(
      <SafeLink 
        href="https://example.com" 
        className="custom-class"
        data-testid="test-link"
      >
        Link
      </SafeLink>
    )
    
    const link = screen.getByTestId("test-link")
    expect(link).toHaveClass("custom-class")
    expect(link.tagName).toBe("A")
  })
})

