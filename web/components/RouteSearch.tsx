"use client";
import { useState } from "react";
import { inr, monthLabel, stopsLabel } from "@/lib/format";

type SearchResult = {
  origin: string;
  destination: string;
  travel_month: string;
  price_inr: number;
  stops: number;
  airline: string | null;
  affiliate_url: string;
  tag?: "lucky" | "mistake" | "regular";
};

type Airport = { iata: string; city: string; name: string; country: string };

const BASE =
  typeof window !== "undefined"
    ? window.location.origin
    : "https://flyingnode.duckdns.org";

function tagResults(results: SearchResult[]): SearchResult[] {
  if (results.length === 0) return [];
  const sorted = [...results].sort((a, b) => a.price_inr - b.price_inr);
  const median =
    sorted.length >= 3
      ? sorted[Math.floor(sorted.length / 2)].price_inr
      : sorted[sorted.length - 1].price_inr * 1.5;
  return sorted.map((r) => {
    const ratio = r.price_inr / median;
    let tag: "lucky" | "mistake" | "regular" = "regular";
    if (ratio <= 0.3) tag = "lucky";
    else if (ratio <= 0.6) tag = "mistake";
    return { ...r, tag };
  });
}

const TAG_STYLES = {
  lucky: {
    bg: "bg-gradient-to-r from-fn-blue to-fn-blue-dark",
    text: "text-white",
    muted: "text-white/60",
    price: "text-fn-orange",
    badge: "bg-fn-orange text-white",
    badgeText: "✈️ Lucky Ticket",
    bookBg: "bg-fn-orange text-white",
  },
  mistake: {
    bg: "bg-fn-card",
    text: "text-fn-ink",
    muted: "text-fn-muted",
    price: "text-fn-blue",
    badge: "bg-fn-orange/15 text-fn-orange",
    badgeText: "Mistake Fare",
    bookBg: "bg-fn-blue text-white",
  },
  regular: {
    bg: "bg-fn-card",
    text: "text-fn-ink",
    muted: "text-fn-muted",
    price: "text-fn-ink",
    badge: "",
    badgeText: "",
    bookBg: "bg-fn-bg text-fn-blue",
  },
};

export default function RouteSearch() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [fromSuggestions, setFromSuggestions] = useState<Airport[]>([]);
  const [toSuggestions, setToSuggestions] = useState<Airport[]>([]);
  const [fromCode, setFromCode] = useState("");
  const [toCode, setToCode] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const fetchSuggestions = async (q: string, setter: (a: Airport[]) => void) => {
    if (q.length < 2) {
      setter([]);
      return;
    }
    const r = await fetch(`${BASE}/airports?q=${encodeURIComponent(q)}`);
    if (r.ok) setter(await r.json());
  };

  const pickFrom = (a: Airport) => {
    setFrom(`${a.city} (${a.iata})`);
    setFromCode(a.iata);
    setFromSuggestions([]);
  };
  const pickTo = (a: Airport) => {
    setTo(`${a.city} (${a.iata})`);
    setToCode(a.iata);
    setToSuggestions([]);
  };

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    const o = fromCode || from.toUpperCase().slice(0, 3);
    const d = toCode || to.toUpperCase().slice(0, 3);
    if (o.length !== 3 || d.length !== 3) return;
    setLoading(true);
    setSearched(true);
    setShowAll(false);
    try {
      const r = await fetch(`${BASE}/search?origin=${o}&destination=${d}`);
      if (r.ok) {
        const raw = await r.json();
        setResults(tagResults(raw));
      } else {
        setResults([]);
      }
    } catch {
      setResults([]);
    }
    setLoading(false);
  };

  const visible = showAll ? results : results.slice(0, 5);

  return (
    <section className="mx-auto max-w-5xl px-6 mb-12">
      <h2 className="font-display text-2xl font-extrabold tracking-tight mb-4">
        Search any route
      </h2>
      <form onSubmit={search} className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-[160px]">
          <input
            type="text"
            value={from}
            onChange={(e) => {
              setFrom(e.target.value);
              setFromCode("");
              fetchSuggestions(e.target.value, setFromSuggestions);
            }}
            placeholder="From (e.g. Ahmedabad)"
            className="w-full px-4 py-3 rounded-lg bg-white shadow-fn text-sm outline-none focus:ring-2 focus:ring-fn-blue/30"
          />
          {fromSuggestions.length > 0 && (
            <ul className="absolute z-10 w-full bg-white shadow-fn-hover rounded-lg mt-1 max-h-48 overflow-y-auto">
              {fromSuggestions.map((a) => (
                <li
                  key={a.iata}
                  onClick={() => pickFrom(a)}
                  className="px-4 py-2 hover:bg-fn-bg cursor-pointer text-sm"
                >
                  <span className="font-semibold">{a.iata}</span> — {a.city},{" "}
                  {a.country}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="relative flex-1 min-w-[160px]">
          <input
            type="text"
            value={to}
            onChange={(e) => {
              setTo(e.target.value);
              setToCode("");
              fetchSuggestions(e.target.value, setToSuggestions);
            }}
            placeholder="To (e.g. Paris)"
            className="w-full px-4 py-3 rounded-lg bg-white shadow-fn text-sm outline-none focus:ring-2 focus:ring-fn-blue/30"
          />
          {toSuggestions.length > 0 && (
            <ul className="absolute z-10 w-full bg-white shadow-fn-hover rounded-lg mt-1 max-h-48 overflow-y-auto">
              {toSuggestions.map((a) => (
                <li
                  key={a.iata}
                  onClick={() => pickTo(a)}
                  className="px-4 py-2 hover:bg-fn-bg cursor-pointer text-sm"
                >
                  <span className="font-semibold">{a.iata}</span> — {a.city},{" "}
                  {a.country}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          disabled={loading}
          className="bg-fn-blue hover:bg-fn-blue-dark text-white px-6 py-3 rounded-lg text-sm font-semibold transition-colors disabled:opacity-60"
        >
          {loading ? "Searching…" : "Find fares"}
        </button>
      </form>

      {searched && !loading && results.length === 0 && (
        <p className="text-fn-muted text-sm">
          No fares found for this route right now. Try a nearby hub (Delhi, Mumbai) or check back later.
        </p>
      )}

      {visible.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-fn-muted uppercase tracking-wider font-semibold">
            {results[0].origin} → {results[0].destination} — {results.length} fare{results.length > 1 ? "s" : ""} found
          </p>
          {visible.map((r, i) => {
            const s = TAG_STYLES[r.tag || "regular"];
            return (
              <a
                key={i}
                href={r.affiliate_url}
                target="_blank"
                rel="noopener sponsored"
                className={`block rounded-card p-5 transition-all hover:-translate-y-0.5 ${s.bg} ${
                  r.tag === "lucky" ? "shadow-fn-hover ring-2 ring-fn-orange/40" : "shadow-fn hover:shadow-fn-hover"
                }`}
              >
                {s.badgeText && (
                  <span className={`inline-block text-xs font-bold px-2.5 py-0.5 rounded-full mb-2 ${s.badge}`}>
                    {s.badgeText}
                  </span>
                )}
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className={`font-display font-bold text-lg ${s.text}`}>
                      {monthLabel(r.travel_month)}
                    </p>
                    <p className={`text-xs ${s.muted}`}>
                      {stopsLabel(r.stops)} · {r.airline ?? "multiple airlines"}
                    </p>
                  </div>
                  <div className="text-right flex items-center gap-3">
                    <span className={`font-display text-2xl font-extrabold ${s.price}`}>
                      {inr(r.price_inr)}
                    </span>
                    <span className={`text-xs font-semibold px-3 py-1.5 rounded-lg ${s.bookBg}`}>
                      Book →
                    </span>
                  </div>
                </div>
              </a>
            );
          })}
          {!showAll && results.length > 5 && (
            <button
              onClick={() => setShowAll(true)}
              className="w-full py-3 text-fn-blue text-sm font-semibold hover:bg-white rounded-lg transition-colors"
            >
              Show {results.length - 5} more fares
            </button>
          )}
          <p className="text-xs text-fn-muted mt-2">
            This route is now being monitored. We'll surface it if a crazy deal drops.
          </p>
        </div>
      )}
    </section>
  );
}
