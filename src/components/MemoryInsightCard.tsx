import type { MemoryAwareCoachingResponse } from "@/types/driving";

export function MemoryInsightCard({
  memory,
  status,
  compact = false,
}: {
  memory: MemoryAwareCoachingResponse | null;
  status: "loading" | "backend" | "fallback";
  compact?: boolean;
}) {
  return (
    <section className="rounded-[24px] border border-forest-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Compared with previous drive</p>
          <h3 className="mt-1 text-sm font-semibold text-ink">Memory-aware coaching</h3>
        </div>
        <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
          {status === "loading" ? "Loading" : memory?.hasMemory ? "Memory on" : "Baseline"}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-700">
        {memory?.memorySummary ?? "Loading previous-drive comparison..."}
      </p>

      {!compact ? (
        <div className="mt-3 grid gap-2">
          <div className="rounded-2xl bg-slate-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Behaviour change</p>
            <p className="mt-1 text-sm leading-5 text-slate-700">
              {memory?.behaviourChangeSummary ?? "Analysing recent score and event movement."}
            </p>
          </div>
          <div className="rounded-2xl bg-forest-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-forest-700">Watch item</p>
            <p className="mt-1 text-sm font-semibold leading-5 text-forest-800">
              {memory?.watchItems?.[0] ?? "Keep collecting comparable route reviews."}
            </p>
          </div>
        </div>
      ) : null}

      <p className="mt-3 text-xs leading-5 text-slate-500">
        {memory?.memoryPolicy ??
          "Recent session memory is used only for measurable pattern comparison, not driver diagnosis or medical inference."}
      </p>
    </section>
  );
}
