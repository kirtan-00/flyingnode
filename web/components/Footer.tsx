import SubscribeForm from "./SubscribeForm";

export default function Footer() {
  return (
    <footer className="mx-auto max-w-5xl px-6 py-16 border-t border-black/5 mt-16">
      <div className="grid gap-8 md:grid-cols-2">
        <div>
          <h3 className="font-display text-2xl font-extrabold tracking-tight">
            Get one email when a deal is worth it.
          </h3>
          <p className="text-fn-muted mt-2 text-sm">
            8am IST, only on days we find something. No "nothing today" emails.
          </p>
          <div className="mt-5">
            <SubscribeForm />
          </div>
        </div>
        <div className="md:text-right text-fn-muted text-sm space-y-2">
          <p>
            <a href="/how-it-works" className="underline underline-offset-2">
              How this works
            </a>
          </p>
          <p>
            <a href="/history" className="underline underline-offset-2">
              Deal history
            </a>
          </p>
          <p>Built by Kirtan.</p>
          <p className="text-xs opacity-60">
            Not a booking agent. We redirect to Google Flights. We may earn a commission.
          </p>
        </div>
      </div>
    </footer>
  );
}
