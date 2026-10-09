import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.BACKEND_API_URL?.trim();
  if (!backendUrl) return NextResponse.json({ error: "Prediction service is not configured." }, { status: 503 });
  try {
    const response = await fetch(`${backendUrl.replace(/\/$/, "")}/investigations/stats`, {
      signal: AbortSignal.timeout(30_000),
      cache: "no-store",
    });
    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
    });
  } catch {
    return NextResponse.json({ error: "Investigation service is unavailable." }, { status: 502 });
  }
}
