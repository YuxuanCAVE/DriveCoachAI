"use client";

import { useMemo, useState } from "react";
import type { PointerEvent } from "react";
import type { RiskEvent, SampleTrip } from "@/types/driving";

type RouteMapCardProps = {
  trip: SampleTrip;
  compact?: boolean;
};

type Point = {
  x: number;
  y: number;
};

type GeoPoint = {
  label?: string;
  lat: number;
  lon: number;
};

const fallbackRoutePoints: Point[] = [
  { x: 372, y: 165 },
  { x: 350, y: 176 },
  { x: 322, y: 173 },
  { x: 296, y: 154 },
  { x: 266, y: 150 },
  { x: 242, y: 164 },
  { x: 222, y: 188 },
  { x: 198, y: 205 },
  { x: 160, y: 204 },
  { x: 126, y: 198 },
  { x: 96, y: 214 },
  { x: 70, y: 242 },
  { x: 48, y: 268 },
];

const eventFallbacks: Record<string, Point> = {
  late_braking_before_curve: { x: 282, y: 153 },
  high_speed_in_curve: { x: 245, y: 162 },
  unstable_cornering: { x: 222, y: 188 },
  harsh_braking: { x: 92, y: 215 },
  harsh_acceleration: { x: 145, y: 201 },
  unstable_speed_control: { x: 70, y: 242 },
  high_lateral_acceleration: { x: 220, y: 188 },
  sharp_yaw_motion: { x: 210, y: 194 },
};

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.floor(seconds % 60);
  return `${minutes}:${remaining.toString().padStart(2, "0")}`;
}

function markerPoint(event: RiskEvent): Point {
  return eventFallbacks[event.type] ?? { x: 190, y: 200 };
}

function isGeoPoint(value: unknown): value is GeoPoint {
  const point = value as GeoPoint;
  return typeof point?.lat === "number" && typeof point?.lon === "number";
}

function projectGeometry(points: GeoPoint[]): Point[] {
  if (points.length < 2) {
    return fallbackRoutePoints;
  }

  const project = createProjector(points);
  return points.map(project);
}

function createProjector(points: GeoPoint[]): (point: GeoPoint) => Point {
  const minLon = Math.min(...points.map((point) => point.lon));
  const maxLon = Math.max(...points.map((point) => point.lon));
  const minLat = Math.min(...points.map((point) => point.lat));
  const maxLat = Math.max(...points.map((point) => point.lat));
  const padding = 34;
  const width = 420 - padding * 2;
  const height = 310 - padding * 2;
  const lonSpan = maxLon - minLon || 1;
  const latSpan = maxLat - minLat || 1;
  const scale = Math.min(width / lonSpan, height / latSpan);
  const projectedWidth = lonSpan * scale;
  const projectedHeight = latSpan * scale;
  const offsetX = (420 - projectedWidth) / 2;
  const offsetY = (310 - projectedHeight) / 2;

  return (point: GeoPoint) => ({
    x: offsetX + (point.lon - minLon) * scale,
    y: offsetY + (maxLat - point.lat) * scale,
  });
}

function pointAlongRoute(points: Point[], progress: number): Point {
  if (points.length === 0) {
    return { x: 190, y: 200 };
  }
  if (points.length === 1) {
    return points[0];
  }

  const clamped = Math.max(0, Math.min(1, progress));
  const lengths = points.slice(1).map((point, index) => {
    const previous = points[index];
    return Math.hypot(point.x - previous.x, point.y - previous.y);
  });
  const total = lengths.reduce((sum, length) => sum + length, 0);
  let travelled = 0;
  const target = total * clamped;

  for (let index = 0; index < lengths.length; index += 1) {
    const length = lengths[index];
    if (travelled + length >= target) {
      const local = length === 0 ? 0 : (target - travelled) / length;
      const start = points[index];
      const end = points[index + 1];
      return {
        x: start.x + (end.x - start.x) * local,
        y: start.y + (end.y - start.y) * local,
      };
    }
    travelled += length;
  }

  return points[points.length - 1];
}

function routePath(points: Point[]): string {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

function hazardEvents(events: RiskEvent[], compact: boolean): RiskEvent[] {
  const preferred = [
    "late_braking_before_curve",
    "high_speed_in_curve",
    "unstable_cornering",
    "harsh_braking",
    "unstable_speed_control",
  ];

  return [...events]
    .sort((a, b) => {
      const aPriority = preferred.includes(a.type) ? preferred.indexOf(a.type) : 999;
      const bPriority = preferred.includes(b.type) ? preferred.indexOf(b.type) : 999;
      const priority = aPriority - bPriority;
      return priority === 0 ? a.startTime - b.startTime : priority;
    })
    .slice(0, compact ? 3 : 4);
}

function nearestSamplePoint(
  trip: SampleTrip,
  event: RiskEvent,
  projectedRoute: Point[],
  projectGeoPoint: ((point: GeoPoint) => Point) | null,
): Point {
  const nearest = trip.samples.reduce((best, sample) => {
    const distance = Math.abs(sample.timestamp - event.startTime);
    const bestDistance = Math.abs(best.timestamp - event.startTime);
    return distance < bestDistance ? sample : best;
  }, trip.samples[0]);

  if (nearest?.lat !== undefined && nearest.lon !== undefined && projectGeoPoint) {
    return projectGeoPoint({ lat: nearest.lat, lon: nearest.lon });
  }
  if (nearest?.distanceAlongRoute !== undefined) {
    return pointAlongRoute(projectedRoute, nearest.distanceAlongRoute);
  }
  return markerPoint(event);
}

export function RouteMapCard({ trip, compact = false }: RouteMapCardProps) {
  const events = useMemo(() => hazardEvents(trip.events, compact), [trip.events, compact]);
  const geometry = useMemo(() => (trip.route.routeGeometry ?? []).filter(isGeoPoint), [trip.route.routeGeometry]);
  const projectedRoute = useMemo(() => projectGeometry(geometry), [geometry]);
  const projectGeoPoint = useMemo(() => (geometry.length >= 2 ? createProjector(geometry) : null), [geometry]);
  const eventPoints = useMemo(
    () =>
      Object.fromEntries(
        events.map((event) => [event.id, nearestSamplePoint(trip, event, projectedRoute, projectGeoPoint)]),
      ) as Record<string, Point>,
    [events, projectedRoute, projectGeoPoint, trip],
  );
  const mapLabels = useMemo(() => {
    if (!geometry.length) {
      return [
        { label: "North Crawley", point: { x: 335, y: 84 } },
        { label: "Broughton", point: { x: 186, y: 230 } },
        { label: "Milton Keynes", point: { x: 33, y: 252 } },
        { label: "Cranfield", point: { x: 310, y: 176 } },
      ];
    }
    const projected = projectGeometry(geometry);
    return geometry
      .map((point, index) => ({ label: point.label ?? "", point: projected[index] }))
      .filter(({ label }) => /Cranfield|North Crawley|Broughton|Milton Keynes/.test(label))
      .map(({ label, point }) => ({
        label: label.replace(" University", "").replace(" Midsummer Place", ""),
        point,
      }));
  }, [geometry]);
  const [selectedEventId, setSelectedEventId] = useState<string | undefined>(events[0]?.id);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState<{ pointerX: number; pointerY: number; panX: number; panY: number } | null>(
    null,
  );
  const selectedEvent = events.find((event) => event.id === selectedEventId) ?? events[0];

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    setDragStart({ pointerX: event.clientX, pointerY: event.clientY, panX: pan.x, panY: pan.y });
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragStart) return;
    setPan({
      x: Math.max(-28, Math.min(28, dragStart.panX + event.clientX - dragStart.pointerX)),
      y: Math.max(-18, Math.min(18, dragStart.panY + event.clientY - dragStart.pointerY)),
    });
  };

  const stopDrag = () => setDragStart(null);

  return (
    <section className={`rounded-[28px] border border-forest-100 bg-white shadow-card ${compact ? "p-3" : "p-5"}`}>
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-4">
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">
            Generated realistic route scenario
          </p>
          <span className="shrink-0 rounded-full bg-forest-50 px-3 py-1 text-xs font-semibold text-forest-700">
            {trip.route.distanceMiles} mi &middot; {trip.route.durationMinutes} min
          </span>
        </div>

        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
          <div className="rounded-2xl border border-forest-100 bg-forest-50/70 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-forest-700">Origin</p>
            <p className={`${compact ? "text-xs" : "text-sm"} mt-1 font-semibold leading-5 text-ink`}>
              {trip.route.origin}
            </p>
          </div>
          <span className="grid h-8 w-8 place-items-center rounded-full bg-white text-sm font-bold text-forest-700 shadow-sm">
            &rarr;
          </span>
          <div className="rounded-2xl border border-forest-100 bg-white px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-forest-700">Destination</p>
            <p className={`${compact ? "text-xs" : "text-sm"} mt-1 font-semibold leading-5 text-ink`}>
              {trip.route.destination}
            </p>
          </div>
        </div>
      </div>

      <div
        className={`relative mt-4 overflow-hidden rounded-[24px] border border-forest-100 bg-[#e8f6ec] ${
          compact ? "h-56" : "h-72"
        } cursor-grab active:cursor-grabbing`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={stopDrag}
        onPointerCancel={stopDrag}
        role="application"
        aria-label="Interactive route review map"
      >
        <div
          className="absolute inset-[-30px] transition-transform duration-75"
          style={{ transform: `translate(${pan.x}px, ${pan.y}px)` }}
        >
          <svg viewBox="0 0 420 310" className="h-full w-full" aria-hidden="true">
            <rect width="420" height="310" fill="#e8f6ec" />
            <path d="M0 38 C72 58 96 36 156 46 S274 94 420 72" fill="none" stroke="#d7eee0" strokeWidth="44" />
            <path d="M-10 236 C62 218 96 244 150 232 S252 184 430 210" fill="none" stroke="#d7eee0" strokeWidth="56" />
            <path d="M270 -20 C250 42 270 92 310 130 S382 176 410 340" fill="none" stroke="#d1e2da" strokeWidth="7" />
            <path d="M270 -20 C250 42 270 92 310 130 S382 176 410 340" fill="none" stroke="#ffffff" strokeWidth="3" />
            <path d="M28 292 L100 238 L155 228 L200 205 L242 160 L304 132 L404 108" fill="none" stroke="#cfded7" strokeWidth="7" />
            <path d="M28 292 L100 238 L155 228 L200 205 L242 160 L304 132 L404 108" fill="none" stroke="#ffffff" strokeWidth="3" />
            <path d="M-20 118 L70 128 L132 116 L210 102 L292 80 L440 88" fill="none" stroke="#d2e1dc" strokeWidth="6" />
            <path d="M-20 118 L70 128 L132 116 L210 102 L292 80 L440 88" fill="none" stroke="#ffffff" strokeWidth="2" />
            <path d="M118 0 L130 78 L114 130 L128 198 L108 320" fill="none" stroke="#cddbd5" strokeWidth="5" />
            <path d="M118 0 L130 78 L114 130 L128 198 L108 320" fill="none" stroke="#ffffff" strokeWidth="2" />
            <path d="M54 34 C88 48 92 64 118 70" fill="none" stroke="#9bd8df" strokeWidth="3" opacity="0.75" />
            <path d="M22 190 C64 180 88 188 120 176" fill="none" stroke="#9bd8df" strokeWidth="3" opacity="0.65" />
            <path d="M330 224 C352 212 378 218 410 204" fill="none" stroke="#9bd8df" strokeWidth="3" opacity="0.65" />
            <path
              d={routePath(projectedRoute)}
              fill="none"
              stroke="#d7eadf"
              strokeWidth="15"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d={routePath(projectedRoute)}
              fill="none"
              stroke="#056348"
              strokeWidth="7"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {mapLabels.map(({ label, point }) => (
              <text key={label} x={point.x + 8} y={point.y - 8} className="fill-slate-500 text-[12px] font-semibold">
                {label}
              </text>
            ))}
            <circle cx={projectedRoute[0]?.x ?? 372} cy={projectedRoute[0]?.y ?? 165} r="9" fill="#ffffff" stroke="#056348" strokeWidth="5" />
            <circle
              cx={projectedRoute.at(-1)?.x ?? 48}
              cy={projectedRoute.at(-1)?.y ?? 268}
              r="9"
              fill="#ef4444"
              stroke="#ffffff"
              strokeWidth="4"
            />
            {events.map((event) => {
              const point = eventPoints[event.id] ?? markerPoint(event);
              const selected = selectedEvent?.id === event.id;
              return (
                <g key={event.id}>
                  {selected ? <circle cx={point.x} cy={point.y} r="16" fill="#f59e0b" opacity="0.24" /> : null}
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r={selected ? 10 : 8}
                    fill="#f59e0b"
                    stroke="#ffffff"
                    strokeWidth="4"
                  />
                </g>
              );
            })}
          </svg>
        </div>

        <div className="absolute left-3 top-3 rounded-full bg-white/95 px-3 py-1.5 text-[11px] font-semibold text-forest-700 shadow-sm">
          Drag map &middot; select hazard
        </div>

        {events.map((event) => {
          const point = eventPoints[event.id] ?? markerPoint(event);
          return (
            <button
              key={event.id}
              type="button"
              aria-label={`Select ${event.type.replaceAll("_", " ")}`}
              className="absolute h-9 w-9 -translate-x-1/2 -translate-y-1/2 rounded-full"
              style={{
                left: `${(point.x / 420) * 100}%`,
                top: `${(point.y / 310) * 100}%`,
                transform: `translate(calc(-50% + ${pan.x}px), calc(-50% + ${pan.y}px))`,
              }}
              onPointerDown={(pointerEvent) => pointerEvent.stopPropagation()}
              onClick={() => setSelectedEventId(event.id)}
            />
          );
        })}
      </div>

      {selectedEvent ? (
        <div className="mt-3 rounded-3xl border border-amber-100 bg-amber-50/80 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-amber-700">Selected hazard</p>
              <h4 className="mt-1 text-sm font-semibold capitalize text-ink">{selectedEvent.type.replaceAll("_", " ")}</h4>
              <p className="mt-1 text-xs font-semibold text-forest-700">
                {selectedEvent.segmentName} &middot; {formatTime(selectedEvent.startTime)}
              </p>
            </div>
            <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-bold uppercase text-amber-700 shadow-sm">
              {selectedEvent.severity}
            </span>
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-700">{selectedEvent.contextualExplanation}</p>
          <p className="mt-2 text-xs font-semibold leading-5 text-forest-700">{selectedEvent.coachingSuggestion}</p>
        </div>
      ) : null}
    </section>
  );
}
