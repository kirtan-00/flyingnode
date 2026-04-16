export const metadata = {
  title: "How flyingnode works",
};

export default function HowItWorks() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16 prose prose-neutral">
      <h1 className="font-display text-4xl font-extrabold tracking-tight text-fn-ink">
        How this works
      </h1>
      <p className="text-fn-muted mt-4 text-lg">
        flyingnode is not a flight booking platform. It's a small, opinionated bot
        that watches flight prices and only tells you about the good ones.
      </p>
      <ol className="mt-8 space-y-5 text-fn-ink">
        <li>
          <span className="font-semibold text-fn-blue">Every 6 hours</span>, a worker
          checks prices from Delhi, Mumbai and Bengaluru to about 60 international
          destinations.
        </li>
        <li>
          <span className="font-semibold text-fn-blue">A baseline is computed</span>{" "}
          per route and travel month — the rolling 90-day median of prices observed.
        </li>
        <li>
          <span className="font-semibold text-fn-blue">A fare becomes a deal</span>{" "}
          only if it's at least 45% below the baseline, is non-stop or 1-stop, has a
          reasonable layover, and includes check-in baggage.
        </li>
        <li>
          <span className="font-semibold text-fn-blue">You click "Book"</span> and
          we send you to Google Flights / airline / OTA. We don't hold your card.
        </li>
        <li>
          <span className="font-semibold text-fn-blue">We only email when there's
          something worth it.</span> No "nothing today" digests.
        </li>
      </ol>
      <p className="mt-10 text-fn-muted text-sm">
        Prices move fast. Mistake fares disappear within hours. When the site shows
        a price, we've checked it within the last 6 hours — always confirm on the
        booking page before paying.
      </p>
    </main>
  );
}
