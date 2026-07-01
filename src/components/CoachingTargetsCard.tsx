import type { CoachingTargetsResponse } from "@/types/driving";

const priorityStyles = {
  high: "bg-amber-100 text-amber-800 border-amber-200",
  medium: "bg-emerald-50 text-forest-700 border-forest-100",
  low: "bg-slate-100 text-slate-600 border-slate-200",
} as const;

function formatNumber(value: number) {
  return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1);
}

function trendLabel(trend?: string | null) {
  if (trend === "improved") {
    return "Improved vs previous";
  }
  if (trend === "needs_attention") {
    return "Needs attention vs previous";
  }
  if (trend === "unchanged") {
    return "Similar to previous";
  }
  return null;
}

export function CoachingTargetsCard({
  targetsResponse,
  status,
}: {
  targetsResponse: CoachingTargetsResponse | null;
  status: "loading" | "backend" | "fallback";
}) {
  const targets = targetsResponse?.targets ?? [];

  return (
    <section className="rounded-[24px] border border-forest-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Next drive targets</p>
          <h3 className="mt-1 text-sm font-semibold text-ink">Measurable coaching goals</h3>
        </div>
        <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
          {status === "loading" ? "Loading" : status === "backend" ? "Deterministic" : "Fallback"}
        </span>
      </div>

      {targets.length ? (
        <div className="mt-4 space-y-3">
          {targets.map((target) => {
            const trend = trendLabel(target.trendVsPrevious);
            return (
              <article key={target.id} className="rounded-3xl border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold leading-5 text-ink">{target.title}</h4>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{target.measurement}</p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full border px-2 py-1 text-[10px] font-bold uppercase ${
                      priorityStyles[target.priority] ?? priorityStyles.medium
                    }`}
                  >
                    {target.priority}
                  </span>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-2">
                  <div className="rounded-2xl bg-white px-3 py-2">
                    <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Current</p>
                    <p className="mt-1 text-base font-semibold text-ink">
                      {formatNumber(target.baselineValue)} <span className="text-xs font-medium text-slate-500">{target.unit}</span>
                    </p>
                  </div>
                  <div className="rounded-2xl bg-white px-3 py-2">
                    <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Target</p>
                    <p className="mt-1 text-base font-semibold text-forest-700">
                      {formatNumber(target.targetValue)} <span className="text-xs font-medium text-slate-500">{target.unit}</span>
                    </p>
                  </div>
                </div>

                <p className="mt-3 text-sm font-semibold leading-5 text-forest-800">{target.nextAction}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">{target.whyItMatters}</p>

                <div className="mt-3 flex flex-wrap gap-2">
                  {target.routeContext.slice(0, 2).map((context) => (
                    <span key={context} className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                      {context}
                    </span>
                  ))}
                  {trend ? (
                    <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-forest-700">{trend}</span>
                  ) : null}
                </div>
              </article>
            );
          })}
          <p className="text-xs leading-5 text-slate-500">{targetsResponse?.evidencePolicy}</p>
        </div>
      ) : (
        <div className="mt-4 rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">
          Coaching targets will appear after deterministic metrics and risk events are available.
        </div>
      )}
    </section>
  );
}
