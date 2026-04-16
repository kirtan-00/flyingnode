"use client";
import { motion } from "framer-motion";
import type { Deal } from "@/lib/api";
import { inr, monthLabel, stopsLabel } from "@/lib/format";

export default function DealCard({ deal, i }: { deal: Deal; i: number }) {
  return (
    <motion.a
      href={deal.affiliate_url}
      target="_blank"
      rel="noopener sponsored"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.04, ease: "easeOut", duration: 0.4 }}
      className="group block bg-fn-card rounded-card shadow-fn hover:shadow-fn-hover hover:-translate-y-0.5 transition-all p-6"
    >
      <div className="flex items-baseline gap-2 text-xs text-fn-muted font-semibold tracking-wider uppercase">
        <span>{deal.origin}</span>
        <span>→</span>
        <span>{deal.destination}</span>
        <span className="ml-auto text-fn-blue">{monthLabel(deal.travel_month)}</span>
      </div>
      <h3 className="font-display text-2xl font-extrabold mt-2 tracking-tight leading-tight">
        {deal.origin_city} → {deal.dest_city}
      </h3>
      <p className="text-sm text-fn-muted">{deal.dest_country}</p>
      <div className="flex items-baseline flex-wrap gap-x-3 gap-y-1 mt-4">
        <span className="font-display text-4xl font-extrabold text-fn-blue tracking-tight">
          {inr(deal.price_inr)}
        </span>
        <span className="text-fn-muted line-through text-sm">{inr(deal.baseline_inr)}</span>
        <span className="bg-fn-orange text-white text-xs font-bold px-3 py-1 rounded-full">
          {deal.savings_pct}% OFF
        </span>
      </div>
      <p className="text-sm text-fn-muted mt-3">
        {stopsLabel(deal.stops)} · {deal.airline ?? "multiple airlines"}
      </p>
      <span className="inline-block mt-5 bg-fn-blue group-hover:bg-fn-blue-dark text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors">
        Book on Google Flights →
      </span>
    </motion.a>
  );
}
