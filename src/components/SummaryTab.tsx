import { RouteMapCard } from "@/components/RouteMapCard";
import type { SampleTrip } from "@/types/driving";

export function SummaryTab({ trip }: { trip: SampleTrip }) {
  const metrics = trip.metrics;
  const score = Math.round(metrics.overallDrivingScore);
  const mainEvent = trip.events[0];
  const status =
    trip.events.length > 0
      ? `${trip.events.length} route events found. Main review focus: ${mainEvent?.segmentName ?? "route context"}.`
      : "No route risk events detected. This session is a smooth baseline.";

  return (
    <div className="space-y-4">
      <section className="rounded-[28px] bg-white p-4 shadow-sm">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">Summary</p>
        <h3 className="mt-1 text-xl font-semibold text-ink">Route review</h3>
        <p className="mt-2 text-sm leading-5 text-slate-600">{status}</p>
      </section>

      <RouteMapCard trip={trip} compact />

      <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-3xl bg-forest-900 p-4 text-white">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-200">Score</p>
            <p className="mt-2 text-3xl font-semibold">{score}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Context</p>
            <p className="mt-2 text-3xl font-semibold text-ink">{Math.round(metrics.contextAdaptationScore)}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Events</p>
            <p className="mt-2 text-3xl font-semibold text-ink">{metrics.riskEventCount}</p>
          </div>
        </div>

        {mainEvent ? (
          <div className="mt-4 rounded-3xl bg-amber-50 px-4 py-3">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-amber-700">Main opportunity</p>
            <h4 className="mt-1 text-sm font-semibold text-ink">{mainEvent.segmentName}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-600">{mainEvent.contextualExplanation}</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
