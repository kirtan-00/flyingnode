"use client";
import { useEffect, useState } from "react";

const ORIGINS = [
  { iata: "DEL", city: "Delhi" },
  { iata: "BOM", city: "Mumbai" },
  { iata: "BLR", city: "Bengaluru" },
  { iata: "AMD", city: "Ahmedabad" },
];

export default function OriginChips({
  onChange,
}: {
  onChange: (iata: string | null) => void;
}) {
  const [sel, setSel] = useState<string | null>(null);
  useEffect(() => {
    const s = localStorage.getItem("fn:origin");
    setSel(s);
    onChange(s);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const pick = (iata: string | null) => {
    setSel(iata);
    if (iata) localStorage.setItem("fn:origin", iata);
    else localStorage.removeItem("fn:origin");
    onChange(iata);
  };
  const chipBase =
    "px-4 py-2 rounded-full text-sm font-semibold transition-transform active:scale-[0.98]";
  return (
    <div className="flex gap-2 flex-wrap">
      <button
        onClick={() => pick(null)}
        className={`${chipBase} ${!sel ? "bg-fn-blue text-white" : "bg-white text-fn-ink shadow-fn"}`}
      >
        All origins
      </button>
      {ORIGINS.map((o) => (
        <button
          key={o.iata}
          onClick={() => pick(o.iata)}
          className={`${chipBase} ${sel === o.iata ? "bg-fn-blue text-white" : "bg-white text-fn-ink shadow-fn"}`}
        >
          {o.city}
        </button>
      ))}
    </div>
  );
}
