"use client";

import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchMemoryAwareCoaching } from "@/lib/apiClient";
import type { Locale } from "@/lib/i18n";
import { sourceLabel } from "@/lib/i18n";
import { generateLocalMemoryAwareFallback } from "@/lib/memoryAwareFallback";
import { memoryAwareCache } from "@/lib/sessionResultCache";
import type { MemoryAwareCoachingResponse, SampleTrip, ScoreTrendPoint, SessionHistoryRecord } from "@/types/driving";

const copy: Record<
  Locale,
  {
    eyebrow: string;
    title: string;
    body: string;
    compared: string;
    building: string;
    behaviourFallback: string;
    repeatedPattern: string;
    noRepeated: string;
    nextWatch: string;
    keepCollecting: string;
    recentSessions: (count: number) => string;
    events: string;
    empty: string;
    now: string;
    stored: string;
    routeReview: string;
  }
> = {
  en: {
    eyebrow: "History",
    title: "Score trend",
    body: "Recent sessions show measurable changes only; this is not a long-term driver profile.",
    compared: "Compared with last drive",
    building: "Building previous-drive comparison...",
    behaviourFallback: "The agent will summarise score and event movement once history is available.",
    repeatedPattern: "Repeated pattern",
    noRepeated: "No repeated pattern established yet.",
    nextWatch: "Next watch item",
    keepCollecting: "Keep collecting comparable route reviews.",
    recentSessions: (count) => `Recent sessions · ${count} stored`,
    events: "events",
    empty: "Generate another backend session to start the score trend.",
    now: "Now",
    stored: "Stored",
    routeReview: "Route review",
  },
  zh: {
    eyebrow: "历史",
    title: "评分趋势",
    body: "这里只展示可衡量的近期变化，不把它解释为长期驾驶画像。",
    compared: "与上一次行程对比",
    building: "正在生成上一程对比...",
    behaviourFallback: "有历史数据后，Agent 会总结评分和 Risk Event 的变化。",
    repeatedPattern: "重复模式",
    noRepeated: "暂未形成稳定重复模式。",
    nextWatch: "下一次关注点",
    keepCollecting: "继续收集可对比的路线复盘。",
    recentSessions: (count) => `近期行程 / 已存 ${count} 条`,
    events: "个事件",
    empty: "再生成一次后端 session，即可开始形成评分趋势。",
    now: "本次",
    stored: "已保存",
    routeReview: "路线复盘",
  },
};

function chartLabel(point: ScoreTrendPoint, index: number, locale: Locale) {
  return point.isCurrent ? copy[locale].now : `S${index + 1}`;
}

function formatSessionDate(value: string | undefined, locale: Locale) {
  if (!value) {
    return copy[locale].stored;
  }
  return new Intl.DateTimeFormat(locale === "zh" ? "zh-CN" : "en-GB", {
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function historyTitle(record: SessionHistoryRecord, locale: Locale) {
  return record.scenario_label || record.scenario_key || copy[locale].routeReview;
}

export function HistoryTab({ trip, locale }: { trip: SampleTrip; locale: Locale }) {
  const t = copy[locale];
  const [memory, setMemory] = useState<MemoryAwareCoachingResponse | null>(() => generateLocalMemoryAwareFallback(trip));
  const [status, setStatus] = useState<"loading" | "backend" | "fallback">("loading");

  useEffect(() => {
    const cached = memoryAwareCache.get(trip.id);
    if (cached) {
      setMemory(cached.memory);
      setStatus(cached.source);
      return;
    }

    const controller = new AbortController();
    const fallbackMemory = generateLocalMemoryAwareFallback(trip);
    setMemory(fallbackMemory);
    setStatus("loading");

    fetchMemoryAwareCoaching(trip, 6, controller.signal)
      .then((response) => {
        memoryAwareCache.set(trip.id, { memory: response, source: "backend" });
        setMemory(response);
        setStatus("backend");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        memoryAwareCache.set(trip.id, { memory: fallbackMemory, source: "fallback" });
        setMemory(fallbackMemory);
        setStatus("fallback");
      });

    return () => controller.abort();
  }, [trip]);

  const chartData = useMemo(
    () =>
      (memory?.scoreTrend ?? []).map((point, index) => ({
        ...point,
        indexLabel: chartLabel(point, index, locale),
        overallScore: Math.round(Number(point.overallScore ?? 0)),
        longitudinalScore: Math.round(Number(point.longitudinalScore ?? 0)),
        lateralScore: Math.round(Number(point.lateralScore ?? 0)),
      })),
    [memory, locale],
  );

  const previous = memory?.scoreTrend?.filter((point) => !point.isCurrent).at(-1);
  const current = memory?.scoreTrend?.find((point) => point.isCurrent);
  const scoreDelta =
    current?.overallScore != null && previous?.overallScore != null ? Math.round(current.overallScore - previous.overallScore) : null;

  return (
    <div className="space-y-4">
      <section className="rounded-[28px] bg-ink p-5 text-white shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">{t.eyebrow}</p>
          <span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-100">
            {status === "loading" ? sourceLabel("loading", locale) : status === "backend" ? sourceLabel("sqlite", locale) : sourceLabel("fallback", locale)}
          </span>
        </div>
        <h3 className="mt-3 text-xl font-semibold leading-7">{t.title}</h3>
        <p className="mt-1 text-sm leading-5 text-slate-300">{t.body}</p>

        <div className="mt-4 h-44 rounded-3xl border border-white/10 bg-white/5 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.12)" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="indexLabel" tick={{ fontSize: 10, fill: "#cbd5e1" }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#cbd5e1" }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  borderRadius: 14,
                  border: "1px solid rgba(255,255,255,0.18)",
                  background: "#12221b",
                  color: "#fff",
                }}
              />
              <Line type="monotone" dataKey="overallScore" name="Overall" stroke="#34d399" strokeWidth={2.6} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="longitudinalScore" name="Braking" stroke="#93c5fd" strokeWidth={1.8} dot={false} />
              <Line type="monotone" dataKey="lateralScore" name="Lateral" stroke="#fbbf24" strokeWidth={1.8} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-[24px] border border-forest-100 bg-white p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.compared}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{memory?.memorySummary ?? t.building}</h3>
          </div>
          {scoreDelta !== null ? (
            <span
              className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] ${
                scoreDelta >= 0 ? "bg-forest-50 text-forest-700" : "bg-amber-50 text-amber-700"
              }`}
            >
              {scoreDelta >= 0 ? "+" : ""}
              {scoreDelta}
            </span>
          ) : null}
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-600">{memory?.behaviourChangeSummary ?? t.behaviourFallback}</p>

        <div className="mt-3 grid gap-2">
          <div className="rounded-2xl bg-slate-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{t.repeatedPattern}</p>
            <p className="mt-1 text-sm font-semibold leading-5 text-ink">{memory?.repeatedPatterns?.[0] ?? t.noRepeated}</p>
          </div>
          <div className="rounded-2xl bg-forest-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-forest-700">{t.nextWatch}</p>
            <p className="mt-1 text-sm font-semibold leading-5 text-forest-800">{memory?.watchItems?.[0] ?? t.keepCollecting}</p>
          </div>
        </div>
      </section>

      <details className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-ink">{t.recentSessions(memory?.recentSessions?.length ?? 0)}</summary>
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {(memory?.recentSessions ?? []).slice(0, 5).map((record) => (
            <article key={record.id} className="min-w-[132px] rounded-2xl border border-slate-100 bg-slate-50 p-3">
              <p className="truncate text-xs font-semibold text-ink">{historyTitle(record, locale)}</p>
              <p className="mt-1 text-[11px] text-slate-500">{formatSessionDate(record.stored_at, locale)}</p>
              <p className="mt-2 text-xl font-semibold text-forest-700">{Math.round(Number(record.overall_score ?? 0))}</p>
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">
                {record.risk_event_count ?? 0} {t.events}
              </p>
            </article>
          ))}
          {memory?.recentSessions?.length ? null : (
            <div className="rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">{t.empty}</div>
          )}
        </div>
      </details>
    </div>
  );
}
