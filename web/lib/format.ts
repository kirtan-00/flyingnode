export const inr = (n: number) => "₹" + n.toLocaleString("en-IN");

export const monthLabel = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { month: "short", year: "numeric" });
};

export const stopsLabel = (stops: number) =>
  stops === 0 ? "Non-stop" : stops === 1 ? "1 stop" : `${stops} stops`;
