import { NextResponse } from "next/server";

async function forward(request: Request, method: "GET" | "POST") {
  const backendUrl = process.env.BACKEND_API_URL?.trim();
  if (!backendUrl) {
    return NextResponse.json(
      { error: "Prediction service is not configured. Set BACKEND_API_URL in the frontend deployment." },
      { status: 503 },
    );
  }

  let suffix = "/investigations";
  if (method === "GET") {
    const query = new URL(request.url).search;
    suffix += query;
  }
  let body: string | undefined;
  if (method === "POST") {
    try {
      body = JSON.stringify(await request.json());
    } catch {
      return NextResponse.json({ error: "Request body must be valid JSON." }, { status: 400 });
    }
  }

  try {
    const response = await fetch(`${backendUrl.replace(/\/$/, "")}${suffix}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body,
      signal: AbortSignal.timeout(30_000),
      cache: "no-store",
    });
    const responseBody = await response.text();
    return new NextResponse(responseBody, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
    });
  } catch {
    return NextResponse.json({ error: "Investigation service is unavailable." }, { status: 502 });
  }
}

export async function GET(request: Request) {
  return forward(request, "GET");
}

export async function POST(request: Request) {
  return forward(request, "POST");
}
