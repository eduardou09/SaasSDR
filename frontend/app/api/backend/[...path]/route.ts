import { NextRequest, NextResponse } from "next/server";

async function proxy(req: NextRequest, path: string[]) {
  const backendBase = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const target = `${backendBase}/api/v1/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  const auth = req.headers.get("authorization");
  const org = req.headers.get("x-clerk-org-id");
  const contentType = req.headers.get("content-type");

  if (auth) headers.set("authorization", auth);
  if (org) headers.set("x-clerk-org-id", org);
  if (contentType) headers.set("content-type", contentType);

  const method = req.method.toUpperCase();
  const body =
    method === "GET" || method === "HEAD" ? undefined : await req.text();

  let res: Response;
  try {
    res = await fetch(target, {
      method,
      headers,
      body,
      cache: "no-store",
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`[proxy] fetch failed — target=${target} error=${message}`);
    return new NextResponse(
      JSON.stringify({ detail: `Proxy error: ${message}`, target }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }

  const responseBody = await res.text();
  return new NextResponse(responseBody, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxy(req, path);
}

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxy(req, path);
}

export async function PUT(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxy(req, path);
}

export async function PATCH(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxy(req, path);
}

export async function DELETE(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxy(req, path);
}
