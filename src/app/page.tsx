"use client";

import { useEffect, useState } from "react";
import { PhoneDemo } from "@/components/PhoneDemo";
import { compareAndSaveSession, fetchDemoSession } from "@/lib/apiClient";
import type { ScenarioKey } from "@/lib/apiClient";
import { generateSampleTrip } from "@/lib/sampleTripGenerator";
import type { SessionComparison } from "@/types/driving";

const productHighlights = [
  {
    title: "Route-aware trip review",
    body: "Reviews each completed trip in context, connecting route segments, speed choice, vehicle motion, and driving smoothness.",
  },
  {
    title: "Risk-event explanation",
    body: "Detects higher-demand moments such as late braking, unstable cornering, and speed variation, then explains the evidence behind them.",
  },
  {
    title: "AI coaching summary",
    body: "Turns deterministic metrics and event evidence into practical next-drive focus areas, with wearable data as optional context only.",
  },
];

const scenarioOptions: {
  key: ScenarioKey;
  label: string;
  seed: number;
  wearable?: boolean;
}[] = [
  { key: "agent_generated", label: "AI-generated random demo", seed: 9101 },
  { key: "mixed_route_review", label: "Mixed route review", seed: 1024 },
  { key: "smooth_baseline", label: "Smooth baseline", seed: 3101 },
  { key: "harsh_braking", label: "Harsh braking", seed: 3201 },
  { key: "high_lateral_acceleration", label: "High lateral acceleration", seed: 3301 },
  { key: "unstable_speed_control", label: "Unstable speed control", seed: 3401 },
  { key: "wearable_connected", label: "Wearable connected", seed: 3501, wearable: true },
  { key: "wearable_not_connected", label: "Wearable not connected", seed: 3601, wearable: false },
];

export default function Home() {
  const [scenario, setScenario] = useState<ScenarioKey>("agent_generated");
  const [includeWearableData, setIncludeWearableData] = useState(false);
  const [seed, setSeed] = useState(9101);
  const [trip, setTrip] = useState(() =>
    generateSampleTrip({
      includeWearableData: false,
      seed: 9101,
    }),
  );
  const [sessionSource, setSessionSource] = useState<"loading" | "backend" | "fallback">("loading");
  const [comparison, setComparison] = useState<SessionComparison | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setSessionSource("loading");

    fetchDemoSession({
      scenario,
      includeWearableData,
      seed,
      signal: controller.signal,
    })
      .then((backendTrip) => {
        setTrip(backendTrip);
        setSessionSource("backend");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setTrip(
          generateSampleTrip({
            includeWearableData,
            seed,
          }),
        );
        setSessionSource("fallback");
      });

    return () => controller.abort();
  }, [scenario, includeWearableData, seed]);

  useEffect(() => {
    if (sessionSource !== "backend") {
      return;
    }

    const controller = new AbortController();
    compareAndSaveSession(trip, controller.signal)
      .then((sessionComparison) => setComparison(sessionComparison))
      .catch(() => setComparison(null));

    return () => controller.abort();
  }, [trip, sessionSource]);

  const regenerate = () => {
    setScenario("agent_generated");
    setSeed(Math.floor(Date.now() % 900000) + 10000);
  };

  const toggleWearable = () => {
    setIncludeWearableData((current) => !current);
    setSeed((current) => current + 19);
  };

  const selectScenario = (nextScenario: ScenarioKey) => {
    const option = scenarioOptions.find((candidate) => candidate.key === nextScenario);
    setScenario(nextScenario);
    setSeed(option?.seed ?? 1024);
    if (typeof option?.wearable === "boolean") {
      setIncludeWearableData(option.wearable);
    }
  };

  return (
    <main>
      <section className="mx-auto grid min-h-screen max-w-6xl items-center gap-12 px-6 py-10 lg:grid-cols-[1fr_440px]">
        <div>
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-ink md:text-6xl">
            Human-Centred AI Driving Coach
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            A post-drive AI coaching product that turns connected-vehicle telemetry into clear driving behaviour insights and personalised improvement suggestions.
          </p>

          <label className="mt-7 flex max-w-md cursor-pointer items-center justify-between rounded-3xl border border-slate-200 bg-white p-4 shadow-card">
            <span>
              <span className="block text-sm font-semibold text-ink">Enable optional wearable data</span>
              <span className="mt-1 block text-xs leading-5 text-slate-500">
                Adds heart-rate context to Driver State. Vehicle telemetry remains the core analysis source.
              </span>
            </span>
            <button
              type="button"
              aria-pressed={includeWearableData}
              onClick={toggleWearable}
              className={`relative h-8 w-14 rounded-full transition ${
                includeWearableData ? "bg-forest-700" : "bg-slate-200"
              }`}
            >
              <span
                className={`absolute top-1 h-6 w-6 rounded-full bg-white shadow-sm transition ${
                  includeWearableData ? "left-7" : "left-1"
                }`}
              />
            </button>
          </label>

          <label className="mt-4 block max-w-md rounded-3xl border border-slate-200 bg-white p-4 shadow-card">
            <span className="block text-sm font-semibold text-ink">Ground-truth scenario</span>
            <span className="mt-1 block text-xs leading-5 text-slate-500">
              Use fixed scenarios for testing, or AI-generated demo sessions for memory comparison.
            </span>
            <select
              value={scenario}
              onChange={(event) => selectScenario(event.target.value as ScenarioKey)}
              className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-ink outline-none transition focus:border-forest-400"
            >
              {scenarioOptions.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mx-auto flex w-full max-w-[470px] flex-col items-center">
          <button
            type="button"
            onClick={regenerate}
            disabled={sessionSource === "loading"}
            className="mb-2 rounded-full bg-forest-700 px-7 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-900/15 transition hover:bg-forest-600 disabled:cursor-wait disabled:bg-forest-500"
          >
            {sessionSource === "loading" ? "Generating Sample Trip" : "Regenerate Sample Trip"}
          </button>
          <p className="mb-4 text-xs font-semibold text-slate-500">
            {sessionSource === "backend"
              ? "Live FastAPI backend session"
              : sessionSource === "fallback"
                ? "Local TypeScript fallback session"
                : "Requesting backend analysis"}
          </p>
          {comparison ? (
            <div className="mb-4 w-full rounded-3xl border border-forest-100 bg-white p-4 shadow-card">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-forest-700">Session memory</p>
                <span className="rounded-full bg-forest-50 px-3 py-1 text-xs font-bold text-forest-700">
                  SQLite
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold text-ink">
                {comparison.hasPrevious ? "Compared with previous session" : "Baseline session stored"}
              </p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{comparison.insights[0]}</p>
            </div>
          ) : null}
          <PhoneDemo trip={trip} />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="rounded-[32px] border border-forest-100 bg-white/85 p-5 shadow-card md:p-6">
          <div className="mb-5 flex flex-col justify-between gap-3 md:flex-row md:items-end">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.18em] text-forest-700">Product overview</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">From route context to risk explanation to coaching summary.</h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-slate-500">
              DriveCoach AI is designed to help users understand what happened during a trip, why it matters, and what to improve next.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {productHighlights.map((item, index) => (
              <article key={item.title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-forest-700 text-xs font-bold text-white">
                  {index + 1}
                </span>
                <h3 className="mt-4 text-base font-semibold text-ink">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
