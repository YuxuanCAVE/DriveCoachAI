const steps = [
  {
    title: "Trip auto-captured",
    body: "Connected-vehicle telemetry is collected after the drive from the vehicle, CAN stream, or simulation logs.",
  },
  {
    title: "Vehicle behaviour analysed",
    body: "Deterministic metrics quantify smoothness, stability, speed control, and vehicle motion demand.",
  },
  {
    title: "Risk events detected",
    body: "Rule-based thresholds identify braking, acceleration, lateral-demand, yaw, and speed-control events.",
  },
  {
    title: "AI coaching summary generated",
    body: "A coaching layer turns the analysis into clear findings and practical next-session focus areas.",
  },
];

export function HowItWorks() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <div className="max-w-2xl">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-forest-700">How it works</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink">A post-drive coaching flow built around route context.</h2>
      </div>
      <div className="mt-8 grid gap-4 md:grid-cols-4">
        {steps.map((step, index) => (
          <article key={step.title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-forest-700 text-sm font-bold text-white">
              {index + 1}
            </span>
            <h3 className="mt-5 text-lg font-semibold text-ink">{step.title}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-600">{step.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
