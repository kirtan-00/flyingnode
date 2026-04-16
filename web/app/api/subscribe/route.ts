const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "https://flyingnode.duckdns.org";

export async function POST(req: Request) {
  const body = await req.text();
  const r = await fetch(BASE + "/subscribe", {
    method: "POST",
    body,
    headers: { "content-type": "application/json" },
  });
  return new Response(await r.text(), {
    status: r.status,
    headers: { "content-type": "application/json" },
  });
}
