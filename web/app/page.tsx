"use client";
import { useEffect, useState } from "react";
import OriginChips from "@/components/OriginChips";
import DealCard from "@/components/DealCard";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
import RouteSearch from "@/components/RouteSearch";
import { listDeals, type Deal } from "@/lib/api";

export default function Home() {
  const [origin, setOrigin] = useState<string | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr(null);
    listDeals(origin ?? undefined)
      .then((d) => {
        if (!alive) return;
        setDeals(d);
        setLoading(false);
      })
      .catch((e) => {
        if (!alive) return;
        setErr(String(e.message ?? e));
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [origin]);

  const luckyTickets = deals.filter((d) => d.savings_pct >= 70);
  const mistakeFares = deals.filter((d) => d.savings_pct < 70);

  return (
    <main>
      <Hero />
      <div className="mx-auto max-w-5xl px-6 pb-8">
        <OriginChips onChange={setOrigin} />
      </div>

      {/* Route search */}
      <RouteSearch />

      {loading && (
        <p className="mx-auto max-w-5xl px-6 text-fn-muted">Looking for deals…</p>
      )}
      {!loading && err && (
        <p className="mx-auto max-w-5xl px-6 text-fn-muted">
          We couldn't reach the API right now. Back shortly.
        </p>
      )}

      {/* Lucky Tickets — ≥70% off */}
      {luckyTickets.length > 0 && (
        <section className="mx-auto max-w-5xl px-6 mb-12">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">✈️</span>
            <div>
              <h2 className="font-display text-2xl font-extrabold tracking-tight">
                Lucky Tickets
              </h2>
              <p className="text-fn-muted text-sm">
                Prices so low they shouldn't exist. Grab before they vanish.
              </p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {luckyTickets.map((d, i) => (
              <DealCard key={d.id} deal={d} i={i} lucky />
            ))}
          </div>
        </section>
      )}

      {/* Mistake Fares — 45-69% off */}
      {mistakeFares.length > 0 && (
        <section className="mx-auto max-w-5xl px-6 mb-12">
          <h2 className="font-display text-2xl font-extrabold tracking-tight mb-4">
            <span className="text-fn-orange">Mistake fares</span> right now
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {mistakeFares.map((d, i) => (
              <DealCard key={d.id} deal={d} i={i} />
            ))}
          </div>
        </section>
      )}

      {!loading && !err && deals.length === 0 && (
        <p className="mx-auto max-w-5xl px-6 text-fn-muted mb-12">
          No deals right now. Search a route above or check back in a few hours.
        </p>
      )}

      <Footer />
    </main>
  );
}
