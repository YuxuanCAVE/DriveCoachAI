import { RouteMapCard } from "@/components/RouteMapCard";
import type { Locale } from "@/lib/i18n";
import type { SampleTrip } from "@/types/driving";

const copy: Record<
  Locale,
  {
    eyebrow: string;
    title: string;
    noEvents: string;
    routeEventsFound: (count: number, segment: string) => string;
    score: string;
    context: string;
    events: string;
    mainOpportunity: string;
  }
> = {
  en: {
    eyebrow: "Summary",
    title: "Route review",
    noEvents: "No route risk events detected. This session is a smooth baseline.",
    routeEventsFound: (count, segment) => `${count} route events found. Main review focus: ${segment}.`,
    score: "Score",
    context: "Context",
    events: "Events",
    mainOpportunity: "Main opportunity",
  },
  zh: {
    eyebrow: "概览",
    title: "路线复盘",
    noEvents: "未检测到路线 Risk Event。本次行程接近平顺基准。",
    routeEventsFound: (count, segment) => `检测到 ${count} 个路线 Risk Event，主要复盘重点：${segment}。`,
    score: "评分",
    context: "场景",
    events: "事件",
    mainOpportunity: "主要改进机会",
  },
};

export function SummaryTab({ trip, locale }: { trip: SampleTrip; locale: Locale }) {
  const metrics = trip.metrics;
  const score = Math.round(metrics.overallDrivingScore);
  const mainEvent = trip.events[0];
  const t = copy[locale];
  const status =
    trip.events.length > 0
      ? t.routeEventsFound(trip.events.length, mainEvent?.segmentName ?? "route context")
      : t.noEvents;

  return (
    <div className="space-y-4">
      <section className="rounded-[28px] bg-white p-4 shadow-sm">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">{t.eyebrow}</p>
        <h3 className="mt-1 text-xl font-semibold text-ink">{t.title}</h3>
        <p className="mt-2 text-sm leading-5 text-slate-600">{status}</p>
      </section>

      <RouteMapCard trip={trip} compact locale={locale} />

      <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-3xl bg-forest-900 p-4 text-white">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-200">{t.score}</p>
            <p className="mt-2 text-3xl font-semibold">{score}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{t.context}</p>
            <p className="mt-2 text-3xl font-semibold text-ink">{Math.round(metrics.contextAdaptationScore)}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{t.events}</p>
            <p className="mt-2 text-3xl font-semibold text-ink">{metrics.riskEventCount}</p>
          </div>
        </div>

        {mainEvent ? (
          <div className="mt-4 rounded-3xl bg-amber-50 px-4 py-3">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-amber-700">{t.mainOpportunity}</p>
            <h4 className="mt-1 text-sm font-semibold text-ink">{mainEvent.segmentName}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-600">{mainEvent.contextualExplanation}</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
