import { NextResponse } from "next/server"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://agitracker-production-6efa.up.railway.app"

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/predictions/accuracy`, {
      next: { revalidate: 3600 } // Cache for 1 hour
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: `Backend error: ${response.statusText}`, details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching prediction accuracy:", error)
    return NextResponse.json(
      { error: "Failed to fetch accuracy", details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
