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
};

type Airport = { iata: string; city: string; name: string; country: string };

const BASE =
  typeof window !== "undefined"
    ? window.location.origin
    : "https://flyingnode.duckdns.org";

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

  const fetchSuggestions = async (q: string, setter: (a: Airport[]) => void) => {
    if (q.length < 2) { setter([]); return; }
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
    try {
      const r = await fetch(`${BASE}/search?origin=${o}&destination=${d}`);
      if (r.ok) setResults(await r.json());
      else setResults([]);
    } catch {
      setResults([]);
    }
    setLoading(false);
  };

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
          No fares found for this route. Travelpayouts may not track it, or no
          flights are available in the next 6 months.
        </p>
      )}

      {results.length > 0 && (
        <div className="bg-fn-card rounded-card shadow-fn p-6">
          <p className="text-xs text-fn-muted mb-4 uppercase tracking-wider font-semibold">
            {results[0].origin} → {results[0].destination} — next 6 months
          </p>
          {results.map((r, i) => (
            <a
              key={i}
              href={r.affiliate_url}
              target="_blank"
              rel="noopener sponsored"
              className="flex items-center justify-between py-3 border-b border-black/5 last:border-0 hover:bg-fn-bg -mx-2 px-2 rounded-lg transition-colors"
            >
              <div>
                <p className="font-semibold">{monthLabel(r.travel_month)}</p>
                <p className="text-xs text-fn-muted">
                  {stopsLabel(r.stops)} · {r.airline ?? "multiple airlines"}
                </p>
              </div>
              <div className="text-right">
                <span className="font-display text-xl font-extrabold text-fn-blue">
                  {inr(r.price_inr)}
                </span>
                <p className="text-xs text-fn-blue">Book →</p>
              </div>
            </a>
          ))}
          <p className="text-xs text-fn-muted mt-4">
            This route is now being monitored. We'll alert you if a crazy deal
            drops.
          </p>
        </div>
      )}
    </section>
  );
}
