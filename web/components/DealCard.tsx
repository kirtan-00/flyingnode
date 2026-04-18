"use client";
import { motion } from "framer-motion";
import type { Deal } from "@/lib/api";
import { inr, monthLabel, stopsLabel } from "@/lib/format";

export default function DealCard({ deal, i, lucky }: { deal: Deal; i: number; lucky?: boolean }) {
  return (
    <motion.a
      href={deal.affiliate_url}
      target="_blank"
      rel="noopener sponsored"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.04, ease: "easeOut", duration: 0.4 }}
      className={`group block rounded-card hover:-translate-y-0.5 transition-all p-6 ${
        lucky
          ? "bg-gradient-to-br from-fn-blue to-fn-blue-dark text-white shadow-fn-hover ring-2 ring-fn-orange/40"
          : "bg-fn-card shadow-fn hover:shadow-fn-hover"
      }`}
    >
      {lucky && (
        <span className="inline-block text-xs font-bold text-fn-orange mb-2 tracking-wider uppercase">
          ✈️ Lucky Ticket
        </span>
      )}
      <div className={`flex items-baseline gap-2 text-xs font-semibold tracking-wider uppercase ${lucky ? "text-white/60" : "text-fn-muted"}`}>
        <span>{deal.origin}</span>
        <span>→</span>
        <span>{deal.destination}</span>
        <span className={`ml-auto ${lucky ? "text-fn-orange" : "text-fn-blue"}`}>{monthLabel(deal.travel_month)}</span>
      </div>
      <h3 className="font-display text-2xl font-extrabold mt-2 tracking-tight leading-tight">
        {deal.origin_city} → {deal.dest_city}
      </h3>
      <p className={`text-sm ${lucky ? "text-white/50" : "text-fn-muted"}`}>{deal.dest_country}</p>
      <div className="flex items-baseline flex-wrap gap-x-3 gap-y-1 mt-4">
        <span className={`font-display text-4xl font-extrabold tracking-tight ${lucky ? "text-white" : "text-fn-blue"}`}>
          {inr(deal.price_inr)}
        </span>
        <span className={`line-through text-sm ${lucky ? "text-white/40" : "text-fn-muted"}`}>{inr(deal.baseline_inr)}</span>
        <span className="bg-fn-orange text-white text-xs font-bold px-3 py-1 rounded-full">
          {deal.savings_pct}% OFF
        </span>
      </div>
      <p className={`text-sm mt-3 ${lucky ? "text-white/60" : "text-fn-muted"}`}>
        {stopsLabel(deal.stops)} · {deal.airline ?? "multiple airlines"}
      </p>
      <span className={`inline-block mt-5 px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors ${lucky ? "bg-fn-orange text-white" : "bg-fn-blue group-hover:bg-fn-blue-dark text-white"}`}>
        Book on Google Flights →
      </span>
    </motion.a>
  );
}
