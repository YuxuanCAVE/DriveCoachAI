import { EventCard } from "@/components/EventCard";
import { MetricCard } from "@/components/MetricCard";
import { RouteMapCard } from "@/components/RouteMapCard";
import { TripChart } from "@/components/TripChart";
import type { Locale } from "@/lib/i18n";
import { sourceLabel } from "@/lib/i18n";
import type { SampleTrip } from "@/types/driving";

const copy: Record<
  Locale,
  {
    eyebrow: string;
    title: string;
    statusWearable: string;
    statusVehicleOnly: string;
    mainTelemetry: string;
    speedMotion: string;
    speedStd: string;
    speed: string;
    accelerationDetails: string;
    longitudinalAx: string;
    lateralAy: string;
    routeContext: string;
    mapEvents: string;
    events: string;
    eventList: string;
    driverState: string;
    wearableContext: string;
    heartRate: string;
    baselineHr: string;
    first60: string;
    maxHr: string;
    demoWearable: string;
    vehicleOnlyNote: string;
  }
> = {
  en: {
    eyebrow: "Drive data",
    title: "Session record",
    statusWearable: "Vehicle telemetry and optional wearable context are available for this session.",
    statusVehicleOnly: "Vehicle telemetry is the primary record. Wearable data is not connected.",
    mainTelemetry: "Main telemetry",
    speedMotion: "Speed and motion demand",
    speedStd: "km/h std",
    speed: "Speed",
    accelerationDetails: "Acceleration and lateral demand",
    longitudinalAx: "Longitudinal ax",
    lateralAy: "Lateral ay",
    routeContext: "Route context",
    mapEvents: "Map and selected events",
    events: "events",
    eventList: "Event list",
    driverState: "Driver state",
    wearableContext: "Optional wearable context",
    heartRate: "Heart rate",
    baselineHr: "Baseline HR",
    first60: "First 60 seconds",
    maxHr: "Max HR",
    demoWearable: "Demo wearable signal",
    vehicleOnlyNote: "This session is analysed using connected-vehicle telemetry only.",
  },
  zh: {
    eyebrow: "行车数据",
    title: "本次行程记录",
    statusWearable: "本次行程包含车辆遥测和可选穿戴数据。",
    statusVehicleOnly: "本次分析以车辆遥测为主，未连接穿戴数据。",
    mainTelemetry: "核心遥测",
    speedMotion: "速度与车辆动态需求",
    speedStd: "km/h 波动",
    speed: "速度",
    accelerationDetails: "加速度与横向需求",
    longitudinalAx: "纵向加速度 ax",
    lateralAy: "横向加速度 ay",
    routeContext: "路线场景",
    mapEvents: "地图与选中事件",
    events: "个事件",
    eventList: "事件列表",
    driverState: "驾驶状态",
    wearableContext: "可选穿戴数据",
    heartRate: "心率",
    baselineHr: "基线心率",
    first60: "前 60 秒",
    maxHr: "最高心率",
    demoWearable: "示例穿戴信号",
    vehicleOnlyNote: "本次行程仅使用 connected-vehicle telemetry 进行分析。",
  },
};

export function DriveDataTab({ trip, locale }: { trip: SampleTrip; locale: Locale }) {
  const metrics = trip.metrics;
  const t = copy[locale];
  const status = metrics.wearableConnected ? t.statusWearable : t.statusVehicleOnly;

  return (
    <div className="space-y-4">
      <section className="rounded-[28px] bg-white p-4 shadow-sm">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">{t.eyebrow}</p>
        <h3 className="mt-1 text-xl font-semibold text-ink">{t.title}</h3>
        <p className="mt-2 text-sm leading-5 text-slate-600">{status}</p>
      </section>

      <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.mainTelemetry}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{t.speedMotion}</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-3 py-1 text-xs font-semibold text-forest-700">
            {(metrics.speedStd * 3.6).toFixed(1)} {t.speedStd}
          </span>
        </div>

        <div className="mt-3">
          <TripChart
            samples={trip.samples}
            events={trip.events}
            series={[{ key: "speed", label: t.speed, color: "#087f5b" }]}
            yUnit=" km/h"
            showSegmentBands
          />
        </div>

        <details className="mt-3 rounded-2xl bg-slate-50 px-3 py-2">
          <summary className="cursor-pointer text-sm font-semibold text-ink">{t.accelerationDetails}</summary>
          <TripChart
            samples={trip.samples}
            events={trip.events}
            series={[
              { key: "ax", label: t.longitudinalAx, color: "#2563eb" },
              { key: "ay", label: t.lateralAy, color: "#f59e0b" },
            ]}
            yUnit=" m/s^2"
            showSegmentBands
          />
        </details>
      </section>

      <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.routeContext}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{t.mapEvents}</h3>
          </div>
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
            {trip.events.length} {t.events}
          </span>
        </div>
        <div className="mt-3">
          <RouteMapCard trip={trip} compact locale={locale} />
        </div>

        <details className="mt-3 rounded-2xl bg-slate-50 px-3 py-2">
          <summary className="cursor-pointer text-sm font-semibold text-ink">{t.eventList}</summary>
          <div className="mt-3 space-y-3">
            {trip.events.slice(0, 4).map((event) => (
              <EventCard key={event.id} event={event} locale={locale} />
            ))}
          </div>
        </details>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.driverState}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{t.wearableContext}</h3>
          </div>
          <span className="rounded-full bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
            {metrics.wearableConnected ? sourceLabel("connected", locale) : sourceLabel("notConnected", locale)}
          </span>
        </div>

        {metrics.wearableConnected ? (
          <>
            <TripChart
              samples={trip.samples}
              events={trip.events}
              series={[{ key: "heartRate", label: t.heartRate, color: "#10b981" }]}
              yUnit=" bpm"
              showEvents
            />
            <div className="mt-3 grid grid-cols-2 gap-3">
              <MetricCard label={t.baselineHr} value={`${metrics.baselineHeartRate?.toFixed(0)} bpm`} helper={t.first60} />
              <MetricCard label={t.maxHr} value={`${metrics.maxHeartRate?.toFixed(0)} bpm`} helper={t.demoWearable} />
            </div>
          </>
        ) : (
          <p className="mt-3 rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">
            {t.vehicleOnlyNote}
          </p>
        )}
      </section>
    </div>
  );
}
