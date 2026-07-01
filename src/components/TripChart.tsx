"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RiskEvent, TripSample } from "@/types/driving";

type TripChartProps = {
  samples: TripSample[];
  events?: RiskEvent[];
  series: Array<{
    key: keyof TripSample;
    label: string;
    color: string;
  }>;
  height?: number;
  yUnit?: string;
  showEvents?: boolean;
  showSegmentBands?: boolean;
};

const eventFill = {
  low: "#d1fae5",
  medium: "#fef3c7",
  high: "#ffe4e6",
};

const segmentFill: Record<string, string> = {
  campus_exit: "#ecfdf5",
  rural_straight: "#f8fafc",
  village_approach: "#fefce8",
  country_curve: "#fff7ed",
  arterial_cruise: "#f0fdf4",
  roundabout_or_junction: "#fef2f2",
  urban_arrival: "#eff6ff",
  destination: "#f5f3ff",
};

function segmentRanges(samples: TripSample[]) {
  const ranges: Array<{ id: string; start: number; end: number; context: string }> = [];
  samples.forEach((sample) => {
    const current = ranges[ranges.length - 1];
    if (current && current.id === sample.segmentId) {
      current.end = sample.timestamp;
      return;
    }
    ranges.push({
      id: sample.segmentId,
      start: sample.timestamp,
      end: sample.timestamp,
      context: sample.roadContext,
    });
  });
  return ranges;
}

export function TripChart({
  samples,
  events = [],
  series,
  height = 190,
  yUnit,
  showEvents = true,
  showSegmentBands = false,
}: TripChartProps) {
  const chartData = samples.map((sample) => ({
    ...sample,
    speedKmh: Number((sample.speed * 3.6).toFixed(1)),
  }));

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 12, right: 8, left: -22, bottom: 0 }}>
          <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="timestamp" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} unit={yUnit} />
          <Tooltip
            contentStyle={{
              borderRadius: 14,
              border: "1px solid #dbe7df",
              boxShadow: "0 14px 34px rgba(15, 23, 42, 0.12)",
            }}
            labelFormatter={(value) => `${value}s`}
          />
          {showSegmentBands
            ? segmentRanges(samples).map((segment) => (
                <ReferenceArea
                  key={segment.id}
                  x1={segment.start}
                  x2={segment.end}
                  fill={segmentFill[segment.context] ?? "#f8fafc"}
                  fillOpacity={0.42}
                  strokeOpacity={0}
                />
              ))
            : null}
          {showEvents
            ? events.slice(0, 8).map((event) => (
                <ReferenceArea
                  key={event.id}
                  x1={event.startTime}
                  x2={event.endTime + 1}
                  fill={eventFill[event.severity]}
                  fillOpacity={0.85}
                  strokeOpacity={0}
                />
              ))
            : null}
          {series.map((item, index) =>
            index === 0 ? (
              <Area
                key={String(item.key)}
                type="monotone"
                dataKey={item.key === "speed" ? "speedKmh" : item.key}
                name={item.label}
                stroke={item.color}
                fill={item.color}
                fillOpacity={0.12}
                strokeWidth={2.4}
                dot={false}
              />
            ) : (
              <Line
                key={String(item.key)}
                type="monotone"
                dataKey={item.key}
                name={item.label}
                stroke={item.color}
                strokeWidth={2}
                dot={false}
              />
            ),
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
