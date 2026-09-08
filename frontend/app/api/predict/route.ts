import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_API_URL;

export async function POST(request: Request) {
  if (!backendUrl) {
    return NextResponse.json(
      { error: "Prediction service is not configured." },
      { status: 503 },
    );
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "Request body must be valid JSON." }, { status: 400 });
  }

  try {
    const response = await fetch(`${backendUrl.replace(/\/$/, "")}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(25_000),
      cache: "no-store",
    });

    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
    });
  } catch {
    return NextResponse.json({ error: "Prediction service is unavailable." }, { status: 502 });
  }
}