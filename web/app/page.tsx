"use client";
import { useEffect, useState } from "react";
import OriginChips from "@/components/OriginChips";
import DealCard from "@/components/DealCard";
import CheapFareRow from "@/components/CheapFareRow";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
import { listDeals, listCheapest, type Deal, type CheapFare } from "@/lib/api";

export default function Home() {
  const [origin, setOrigin] = useState<string | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [cheapest, setCheapest] = useState<CheapFare[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr(null);
    Promise.all([
      listDeals(origin ?? undefined),
      listCheapest(origin ?? undefined),
    ])
      .then(([d, c]) => {
        if (!alive) return;
        setDeals(d);
        setCheapest(c);
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

  return (
    <main>
      <Hero />
      <div className="mx-auto max-w-5xl px-6 pb-8">
        <OriginChips onChange={setOrigin} />
      </div>

      {/* Deals section */}
      {deals.length > 0 && (
        <section className="mx-auto max-w-5xl px-6 mb-12">
          <h2 className="font-display text-2xl font-extrabold tracking-tight mb-4">
            <span className="text-fn-orange">Mistake fares</span> right now
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {deals.map((d, i) => (
              <DealCard key={d.id} deal={d} i={i} />
            ))}
          </div>
        </section>
      )}

      {/* Cheapest fares section */}
      <section className="mx-auto max-w-5xl px-6">
        {loading && <p className="text-fn-muted">Looking for fares…</p>}
        {!loading && err && (
          <p className="text-fn-muted">
            We couldn't reach the API right now. Back shortly.
          </p>
        )}
        {!loading && !err && cheapest.length > 0 && (
          <>
            <h2 className="font-display text-2xl font-extrabold tracking-tight mb-2">
              Cheapest fares we found
            </h2>
            <p className="text-fn-muted text-sm mb-4">
              Updated every 6 hours. Not necessarily deals — just the lowest prices right now.
            </p>
            <div className="bg-fn-card rounded-card shadow-fn p-6">
              {cheapest.map((f, i) => (
                <CheapFareRow key={`${f.origin}-${f.destination}-${f.travel_month}`} fare={f} i={i} />
              ))}
            </div>
          </>
        )}
        {!loading && !err && cheapest.length === 0 && deals.length === 0 && (
          <p className="text-fn-muted">
            No fares yet. The algorithm is watching; check back in a few hours.
          </p>
        )}
      </section>

      <Footer />
    </main>
  );
}
