"use client";
import { useEffect, useState } from "react";
import OriginChips from "@/components/OriginChips";
import DealCard from "@/components/DealCard";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
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

  return (
    <main>
      <Hero />
      <div className="mx-auto max-w-5xl px-6 pb-8">
        <OriginChips onChange={setOrigin} />
      </div>
      <div className="mx-auto max-w-5xl px-6 grid gap-4 md:grid-cols-2">
        {loading && <p className="text-fn-muted">Looking for deals…</p>}
        {!loading && err && (
          <p className="text-fn-muted">
            We couldn't reach the deals API right now. Back shortly.
          </p>
        )}
        {!loading && !err && deals.length === 0 && (
          <p className="text-fn-muted col-span-2">
            No live deals right now. The algorithm is watching; check back in a few hours.
          </p>
        )}
        {deals.map((d, i) => (
          <DealCard key={d.id} deal={d} i={i} />
        ))}
      </div>
      <Footer />
    </main>
  );
}
