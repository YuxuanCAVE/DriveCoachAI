import type { TargetCompletionResponse } from "@/types/driving";

function formatNumber(value: number) {
  return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1);
}

export function TargetCompletionCard({
  completion,
  status,
}: {
  completion: TargetCompletionResponse | null;
  status: "loading" | "backend" | "fallback";
}) {
  const results = completion?.results ?? [];

  return (
    <section className="rounded-[24px] border border-forest-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Target progress</p>
          <h3 className="mt-1 text-sm font-semibold text-ink">Previous target completion</h3>
        </div>
        <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
          {status === "loading" ? "Loading" : `${completion?.completionRate ?? 0}% done`}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-700">
        {completion?.summary ?? "Checking whether the previous target set was completed..."}
      </p>

      {results.length ? (
        <div className="mt-4 space-y-2">
          {results.slice(0, 3).map((result) => (
            <article
              key={result.targetId}
              className={`rounded-3xl border p-3 ${
                result.completed ? "border-emerald-100 bg-emerald-50" : "border-amber-100 bg-amber-50"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold leading-5 text-ink">{result.title}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">{result.measurement}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-bold uppercase ${
                    result.completed ? "bg-white text-forest-700" : "bg-white text-amber-700"
                  }`}
                >
                  {result.completed ? "Completed" : "Continue"}
                </span>
              </div>

              <div className="mt-3 grid grid-cols-3 gap-2">
                <div className="rounded-2xl bg-white px-2.5 py-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Previous</p>
                  <p className="mt-1 text-sm font-semibold text-ink">
                    {formatNumber(result.previousBaselineValue)} <span className="text-[10px] text-slate-500">{result.unit}</span>
                  </p>
                </div>
                <div className="rounded-2xl bg-white px-2.5 py-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Target</p>
                  <p className="mt-1 text-sm font-semibold text-forest-700">
                    {formatNumber(result.targetValue)} <span className="text-[10px] text-slate-500">{result.unit}</span>
                  </p>
                </div>
                <div className="rounded-2xl bg-white px-2.5 py-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Current</p>
                  <p className="mt-1 text-sm font-semibold text-ink">
                    {formatNumber(result.currentValue)} <span className="text-[10px] text-slate-500">{result.unit}</span>
                  </p>
                </div>
              </div>

              <p className="mt-3 text-sm font-semibold leading-5 text-forest-800">{result.nextAction}</p>
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-4 rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">
          No previous target set yet. Generate another session to start target completion tracking.
        </div>
      )}

      {completion?.activeTargets?.length ? (
        <div className="mt-4 rounded-2xl bg-slate-50 px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Next active focus</p>
          <p className="mt-1 text-sm font-semibold leading-5 text-ink">{completion.activeTargets[0].title}</p>
        </div>
      ) : null}

      <p className="mt-3 text-xs leading-5 text-slate-500">
        {completion?.policy ?? "Target progress uses deterministic previous-target measurements and current telemetry metrics."}
      </p>
    </section>
  );
}
