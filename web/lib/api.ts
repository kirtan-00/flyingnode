const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "https://flyingnode.duckdns.org";

export type Deal = {
  id: number;
  origin: string;
  destination: string;
  origin_city: string;
  origin_name?: string;
  dest_city: string;
  dest_name?: string;
  dest_country: string;
  price_inr: number;
  baseline_inr: number;
  savings_pct: number;
  stops: number;
  airline: string | null;
  travel_month: string;
  affiliate_url: string;
  first_seen_at: string;
};

export type DealWithHistory = Deal & {
  history: { observed_at: string; price_inr: number }[];
};

export async function listDeals(origin?: string): Promise<Deal[]> {
  const url = new URL(BASE + "/deals");
  if (origin) url.searchParams.set("origin", origin);
  const r = await fetch(url.toString(), { next: { revalidate: 600 } });
  if (!r.ok) throw new Error("deals fetch failed: " + r.status);
  return r.json();
}

export async function getDeal(id: number): Promise<DealWithHistory> {
  const r = await fetch(`${BASE}/deal/${id}`, { next: { revalidate: 600 } });
  if (!r.ok) throw new Error("deal fetch failed: " + r.status);
  return r.json();
}
