"use client";
import { useEffect, useState } from "react";
import { inr, monthLabel, stopsLabel } from "@/lib/format";

const BASE =
  typeof window !== "undefined"
    ? window.location.origin
    : "https://flyingnode.duckdns.org";

type PastDeal = {
  id: number;
  origin: string;
  destination: string;
  origin_city: string;
  dest_city: string;
  dest_country: string;
  price_inr: number;
  baseline_inr: number;
  savings_pct: number;
  stops: number;
  airline: string | null;
  travel_month: string;
  first_seen_at: string;
  last_seen_at: string;
};

export default function History() {
  const [deals, setDeals] = useState<PastDeal[]>([]);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = async (p: number) => {
    setLoading(true);
    const r = await fetch(`${BASE}/deal-history?page=${p}`);
    if (r.ok) {
      const d = await r.json();
      setDeals(d);
      setPage(p);
    }
    setLoading(false);
  };

  useEffect(() => { load(0); }, []);

  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <a href="/" className="text-fn-blue text-sm font-semibold mb-6 inline-block">
        ← Back to deals
      </a>
      <h1 className="font-display text-4xl font-extrabold tracking-tight text-fn-ink mb-2">
        Deal history
      </h1>
      <p className="text-fn-muted mb-8">
        Every crazy deal we've found, archived. Prices may no longer be available.
      </p>

      {loading && <p className="text-fn-muted">Loading…</p>}

      {!loading && deals.length === 0 && (
        <p className="text-fn-muted">
          No past deals yet. The system just started monitoring — check back in a few days.
        </p>
      )}

      {deals.length > 0 && (
        <div className="bg-fn-card rounded-card shadow-fn divide-y divide-black/5">
          {deals.map((d) => (
            <div key={d.id} className="p-5 flex items-center justify-between gap-4">
              <div>
                <p className="font-display font-bold text-lg tracking-tight">
                  {d.origin_city} → {d.dest_city}
                </p>
                <p className="text-xs text-fn-muted">
                  {d.origin} → {d.destination} · {stopsLabel(d.stops)} ·{" "}
                  {d.airline ?? "varied"} · {monthLabel(d.travel_month)}
                </p>
                <p className="text-xs text-fn-muted mt-1">
                  Found {new Date(d.first_seen_at).toLocaleDateString("en-IN")}
                  {d.last_seen_at !== d.first_seen_at &&
                    ` — lasted until ${new Date(d.last_seen_at).toLocaleDateString("en-IN")}`}
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="font-display text-2xl font-extrabold text-fn-blue">
                  {inr(d.price_inr)}
                </span>
                <p className="text-fn-muted line-through text-xs">{inr(d.baseline_inr)}</p>
                <span className="bg-fn-orange/20 text-fn-orange text-xs font-bold px-2 py-0.5 rounded-full">
                  was {d.savings_pct}% off
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {deals.length >= 30 && (
        <div className="flex gap-3 mt-6 justify-center">
          {page > 0 && (
            <button
              onClick={() => load(page - 1)}
              className="px-4 py-2 bg-white shadow-fn rounded-lg text-sm font-semibold"
            >
              ← Newer
            </button>
          )}
          <button
            onClick={() => load(page + 1)}
            className="px-4 py-2 bg-white shadow-fn rounded-lg text-sm font-semibold"
          >
            Older →
          </button>
        </div>
      )}
    </main>
  );
}
