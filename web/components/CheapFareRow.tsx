"use client";
import { motion } from "framer-motion";
import type { CheapFare } from "@/lib/api";
import { inr, monthLabel, stopsLabel } from "@/lib/format";

export default function CheapFareRow({ fare, i }: { fare: CheapFare; i: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: i * 0.03 }}
      className="flex items-center justify-between py-4 border-b border-black/5 last:border-0"
    >
      <div>
        <p className="font-display font-bold text-lg tracking-tight">
          {fare.origin_city} → {fare.dest_city}
        </p>
        <p className="text-xs text-fn-muted">
          {fare.origin} → {fare.destination} · {stopsLabel(fare.stops)} · {fare.airline ?? "varied"} · {monthLabel(fare.travel_month)}
        </p>
      </div>
      <span className="font-display text-xl font-extrabold text-fn-blue tracking-tight whitespace-nowrap ml-4">
        {inr(fare.price_inr)}
      </span>
    </motion.div>
  );
}
