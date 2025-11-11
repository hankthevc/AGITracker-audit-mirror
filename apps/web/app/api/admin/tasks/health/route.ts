import { NextRequest, NextResponse } from "next/server"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://agitracker-production-6efa.up.railway.app"

// Force dynamic rendering since we use request.headers
export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const apiKey = request.headers.get("x-api-key")
    
    if (!apiKey) {
      return NextResponse.json(
        { error: "Missing x-api-key header" },
        { status: 401 }
      )
    }

    const response = await fetch(`${API_BASE_URL}/v1/admin/tasks/health`, {
      headers: {
        "x-api-key": apiKey,
      },
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
    console.error("Error fetching task health:", error)
    return NextResponse.json(
      { error: "Failed to fetch task health", details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
