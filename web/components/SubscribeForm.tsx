"use client";
import { useState } from "react";

export default function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "err">("idle");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setState("sending");
    try {
      const r = await fetch("/subscribe", {
        method: "POST",
        body: JSON.stringify({ email }),
        headers: { "content-type": "application/json" },
      });
      setState(r.ok ? "done" : "err");
    } catch {
      setState("err");
    }
  };

  if (state === "done")
    return (
      <p className="text-fn-blue font-semibold">
        You're in. First digest tomorrow 8am IST.
      </p>
    );

  return (
    <form onSubmit={submit} className="flex gap-2 max-w-md">
      <input
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@example.com"
        className="flex-1 px-4 py-3 rounded-lg bg-white shadow-fn text-sm outline-none focus:ring-2 focus:ring-fn-blue/30"
      />
      <button
        disabled={state === "sending"}
        className="bg-fn-blue hover:bg-fn-blue-dark text-white px-5 py-3 rounded-lg text-sm font-semibold transition-colors disabled:opacity-60"
      >
        {state === "sending" ? "…" : "Get deals"}
      </button>
    </form>
  );
}
