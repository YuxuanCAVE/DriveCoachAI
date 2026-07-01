import { EventCard } from "@/components/EventCard";
import { MetricCard } from "@/components/MetricCard";
import { RouteMapCard } from "@/components/RouteMapCard";
import { TripChart } from "@/components/TripChart";
import type { SampleTrip } from "@/types/driving";

export function DriveDataTab({ trip }: { trip: SampleTrip }) {
  const metrics = trip.metrics;
  const status = metrics.wearableConnected
    ? "Vehicle telemetry and optional wearable context are available for this session."
    : "Vehicle telemetry is the primary record. Wearable data is not connected.";

  return (
    <div className="space-y-4">
      <section className="rounded-[28px] bg-white p-4 shadow-sm">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">Drive data</p>
        <h3 className="mt-1 text-xl font-semibold text-ink">Session record</h3>
        <p className="mt-2 text-sm leading-5 text-slate-600">{status}</p>
      </section>

      <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Main telemetry</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">Speed and motion demand</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-3 py-1 text-xs font-semibold text-forest-700">
            {(metrics.speedStd * 3.6).toFixed(1)} km/h std
          </span>
        </div>

        <div className="mt-3">
          <TripChart
            samples={trip.samples}
            events={trip.events}
            series={[{ key: "speed", label: "Speed", color: "#087f5b" }]}
            yUnit=" km/h"
            showSegmentBands
          />
        </div>

        <details className="mt-3 rounded-2xl bg-slate-50 px-3 py-2">
          <summary className="cursor-pointer text-sm font-semibold text-ink">Acceleration and lateral demand</summary>
          <TripChart
            samples={trip.samples}
            events={trip.events}
            series={[
              { key: "ax", label: "Longitudinal ax", color: "#2563eb" },
              { key: "ay", label: "Lateral ay", color: "#f59e0b" },
            ]}
            yUnit=" m/s^2"
            showSegmentBands
          />
        </details>
      </section>

      <section className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Route context</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">Map and selected events</h3>
          </div>
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
            {trip.events.length} events
          </span>
        </div>
        <div className="mt-3">
          <RouteMapCard trip={trip} compact />
        </div>

        <details className="mt-3 rounded-2xl bg-slate-50 px-3 py-2">
          <summary className="cursor-pointer text-sm font-semibold text-ink">Event list</summary>
          <div className="mt-3 space-y-3">
            {trip.events.slice(0, 4).map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </details>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Driver state</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">Optional wearable context</h3>
          </div>
          <span className="rounded-full bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
            {metrics.wearableConnected ? "Connected" : "Not connected"}
          </span>
        </div>

        {metrics.wearableConnected ? (
          <>
            <TripChart
              samples={trip.samples}
              events={trip.events}
              series={[{ key: "heartRate", label: "Heart rate", color: "#10b981" }]}
              yUnit=" bpm"
              showEvents
            />
            <div className="mt-3 grid grid-cols-2 gap-3">
              <MetricCard label="Baseline HR" value={`${metrics.baselineHeartRate?.toFixed(0)} bpm`} helper="First 60 seconds" />
              <MetricCard label="Max HR" value={`${metrics.maxHeartRate?.toFixed(0)} bpm`} helper="Demo wearable signal" />
            </div>
          </>
        ) : (
          <p className="mt-3 rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">
            This session is analysed using connected-vehicle telemetry only.
          </p>
        )}
      </section>
    </div>
  );
}
