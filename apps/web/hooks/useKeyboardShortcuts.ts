"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export function useKeyboardShortcuts() {
  const router = useRouter()

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      // Don't trigger shortcuts when typing in input fields
      const target = event.target as HTMLElement
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        // Exception: Allow Escape in inputs
        if (event.key !== "Escape") {
          return
        }
      }

      // Cmd/Ctrl + K: Focus search (preventDefault to avoid browser search)
      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault()
        const searchInput = document.querySelector<HTMLInputElement>('input[placeholder*="Search"]')
        if (searchInput) {
          searchInput.focus()
        }
        return
      }

      // / key: Focus search
      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        event.preventDefault()
        const searchInput = document.querySelector<HTMLInputElement>('input[placeholder*="Search"]')
        if (searchInput) {
          searchInput.focus()
        }
        return
      }

      // ? key: Show shortcuts help
      if (event.key === "?" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        event.preventDefault()
        // Show shortcuts modal (could be implemented later)
        alert(`Keyboard Shortcuts:

⌘/Ctrl + K - Focus search
/ - Focus search
? - Show this help
Esc - Close modals/clear search
h - Go to home
e - Go to events
t - Go to timeline
i - Go to insights
m - Go to methodology`)
        return
      }

      // Escape: Clear search or close modals
      if (event.key === "Escape") {
        const searchInput = document.querySelector<HTMLInputElement>('input[placeholder*="Search"]')
        if (searchInput && searchInput.value) {
          searchInput.value = ""
          searchInput.dispatchEvent(new Event("input", { bubbles: true }))
          searchInput.blur()
        }
        return
      }

      // Navigation shortcuts (only when not in input)
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
        return
      }

      // h: Home
      if (event.key === "h") {
        router.push("/")
        return
      }

      // e: Events
      if (event.key === "e") {
        router.push("/events")
        return
      }

      // t: Timeline
      if (event.key === "t") {
        router.push("/timeline")
        return
      }

      // i: Insights
      if (event.key === "i") {
        router.push("/insights")
        return
      }

      // m: Methodology
      if (event.key === "m") {
        router.push("/methodology")
        return
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [router])
}
