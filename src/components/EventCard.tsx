import type { RiskEvent } from "@/types/driving";
import type { Locale } from "@/lib/i18n";
import { eventTypeLabel, severityLabel } from "@/lib/i18n";

const severityStyle = {
  low: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  medium: "bg-amber-50 text-amber-700 ring-amber-200",
  high: "bg-rose-50 text-rose-700 ring-rose-200",
};

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.floor(seconds % 60);
  return `${minutes}:${remaining.toString().padStart(2, "0")}`;
}

export function EventCard({ event, locale }: { event: RiskEvent; locale: Locale }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold text-slate-400">
            {formatTime(event.startTime)}-{formatTime(event.endTime)}
          </p>
          <h4 className="mt-1 text-sm font-semibold text-ink">{eventTypeLabel(event.type, locale)}</h4>
          <p className="mt-1 text-[11px] font-semibold text-forest-700">{event.segmentName}</p>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ring-1 ${severityStyle[event.severity]}`}>
          {severityLabel(event.severity, locale)}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-600">{event.contextualExplanation}</p>
      <p className="mt-2 text-xs font-medium leading-5 text-forest-700">{event.coachingSuggestion}</p>
    </article>
  );
}
