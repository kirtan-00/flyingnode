export default function Hero() {
  return (
    <section className="mx-auto max-w-5xl px-6 pt-16 pb-8">
      <div className="flex items-center gap-2 text-fn-blue font-display font-extrabold text-lg">
        <span className="inline-block w-2 h-2 bg-fn-orange rounded-full" />
        flyingnode
      </div>
      <h1 className="font-display text-5xl md:text-6xl font-extrabold tracking-tight text-fn-ink mt-6 leading-[1.05]">
        Flights so cheap
        <br />
        they feel <span className="text-fn-blue">like a glitch.</span>
      </h1>
      <p className="text-lg text-fn-muted mt-5 max-w-xl leading-relaxed">
        Curated mistake fares from Delhi, Mumbai and Bengaluru. Only the ones worth
        interrupting your day for.
      </p>
    </section>
  );
}
