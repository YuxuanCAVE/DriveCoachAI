"use client";

import { useEffect, useState } from "react";
import { DocumentationSections } from "@/components/DocumentationSections";
import { PhoneDemo } from "@/components/PhoneDemo";
import { compareAndSaveSession, fetchDemoSession } from "@/lib/apiClient";
import type { ScenarioKey } from "@/lib/apiClient";
import type { Locale } from "@/lib/i18n";
import { generateSampleTrip } from "@/lib/sampleTripGenerator";
import type { SessionComparison } from "@/types/driving";

const copy: Record<
  Locale,
  {
    navItems: { label: string; href: string }[];
    heroTitle: string;
    heroBody: string;
    wearableTitle: string;
    wearableBody: string;
    scenarioTitle: string;
    scenarioBody: string;
    regenerate: string;
    generating: string;
    backendStatus: string;
    fallbackStatus: string;
    loadingStatus: string;
    sessionMemory: string;
    sqlite: string;
    compared: string;
    baselineStored: string;
    languageLabel: string;
  }
> = {
  en: {
    navItems: [
      { label: "Demo", href: "#demo" },
      { label: "Product", href: "#product" },
      { label: "Architecture", href: "#architecture" },
      { label: "Agent", href: "#agent" },
      { label: "Evaluation", href: "#evaluation" },
      { label: "Roadmap", href: "#roadmap" },
    ],
    heroTitle: "Human-Centred AI Driving Coach",
    heroBody:
      "A post-drive AI coaching product that turns connected-vehicle telemetry into clear driving behaviour insights and personalised improvement suggestions.",
    wearableTitle: "Enable optional wearable data",
    wearableBody: "Adds heart-rate context to Driver State. Vehicle telemetry remains the core analysis source.",
    scenarioTitle: "Ground-truth scenario",
    scenarioBody: "Use fixed scenarios for testing, or AI-generated demo sessions for memory comparison.",
    regenerate: "Regenerate Sample Trip",
    generating: "Generating Sample Trip",
    backendStatus: "Live FastAPI backend session",
    fallbackStatus: "Local TypeScript fallback session",
    loadingStatus: "Requesting backend analysis",
    sessionMemory: "Session memory",
    sqlite: "SQLite",
    compared: "Compared with previous session",
    baselineStored: "Baseline session stored",
    languageLabel: "Language",
  },
  zh: {
    navItems: [
      { label: "Demo", href: "#demo" },
      { label: "Product", href: "#product" },
      { label: "Architecture", href: "#architecture" },
      { label: "Agent", href: "#agent" },
      { label: "Evaluation", href: "#evaluation" },
      { label: "Roadmap", href: "#roadmap" },
    ],
    heroTitle: "Human-Centred AI Driving Coach",
    heroBody:
      "一个 post-drive AI coaching product，把 connected-vehicle telemetry 转化为清晰的驾驶行为洞察和个性化改进建议。",
    wearableTitle: "启用 optional wearable data",
    wearableBody: "为 Driver State 增加 heart-rate context；vehicle telemetry 仍然是核心分析来源。",
    scenarioTitle: "Ground-truth scenario",
    scenarioBody: "使用固定场景做测试，或使用 AI-generated demo sessions 做 memory comparison。",
    regenerate: "Regenerate Sample Trip",
    generating: "正在生成 Sample Trip",
    backendStatus: "来自 FastAPI backend 的实时 session",
    fallbackStatus: "本地 TypeScript fallback session",
    loadingStatus: "正在请求 backend analysis",
    sessionMemory: "Session memory",
    sqlite: "SQLite",
    compared: "已与上一次 session 对比",
    baselineStored: "已存储 baseline session",
    languageLabel: "Language",
  },
};

const scenarioLabels: Record<Locale, Record<ScenarioKey, string>> = {
  en: {
    agent_generated: "AI-generated random demo",
    mixed_route_review: "Mixed route review",
    smooth_baseline: "Smooth baseline",
    harsh_braking: "Harsh braking",
    high_lateral_acceleration: "High lateral acceleration",
    unstable_speed_control: "Unstable speed control",
    wearable_connected: "Wearable connected",
    wearable_not_connected: "Wearable not connected",
  },
  zh: {
    agent_generated: "AI-generated random demo",
    mixed_route_review: "Mixed route review",
    smooth_baseline: "Smooth baseline",
    harsh_braking: "Harsh braking",
    high_lateral_acceleration: "High lateral acceleration",
    unstable_speed_control: "Unstable speed control",
    wearable_connected: "Wearable connected",
    wearable_not_connected: "Wearable not connected",
  },
};

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
  const [locale, setLocale] = useState<Locale>("en");
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
  const t = copy[locale];

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
      <header className="sticky top-0 z-40 border-b border-forest-100/80 bg-[#f7fbf7]/90 backdrop-blur-xl">
        <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
          <a href="#demo" className="text-sm font-black tracking-tight text-forest-900">
            DriveCoach AI
          </a>
          <div className="no-scrollbar flex items-center gap-2 overflow-x-auto">
            {t.navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-full px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-white hover:text-forest-700 hover:shadow-sm"
              >
                {item.label}
              </a>
            ))}
            <div className="ml-1 flex shrink-0 items-center rounded-full border border-forest-100 bg-white p-1 shadow-sm">
              <span className="sr-only">{t.languageLabel}</span>
              {(["en", "zh"] as const).map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setLocale(item)}
                  className={`rounded-full px-3 py-1.5 text-xs font-bold transition ${
                    locale === item ? "bg-forest-700 text-white" : "text-slate-500 hover:bg-forest-50"
                  }`}
                >
                  {item === "en" ? "EN" : "中文"}
                </button>
              ))}
            </div>
          </div>
        </nav>
      </header>

      <section id="demo" className="mx-auto grid min-h-screen scroll-mt-24 max-w-6xl items-center gap-12 px-6 py-10 lg:grid-cols-[1fr_440px]">
        <div>
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-ink md:text-6xl">
            {t.heroTitle}
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            {t.heroBody}
          </p>

          <label className="mt-7 flex max-w-md cursor-pointer items-center justify-between rounded-3xl border border-slate-200 bg-white p-4 shadow-card">
            <span>
              <span className="block text-sm font-semibold text-ink">{t.wearableTitle}</span>
              <span className="mt-1 block text-xs leading-5 text-slate-500">
                {t.wearableBody}
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
            <span className="block text-sm font-semibold text-ink">{t.scenarioTitle}</span>
            <span className="mt-1 block text-xs leading-5 text-slate-500">
              {t.scenarioBody}
            </span>
            <select
              value={scenario}
              onChange={(event) => selectScenario(event.target.value as ScenarioKey)}
              className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-ink outline-none transition focus:border-forest-400"
            >
              {scenarioOptions.map((option) => (
                <option key={option.key} value={option.key}>
                  {scenarioLabels[locale][option.key]}
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
            {sessionSource === "loading" ? t.generating : t.regenerate}
          </button>
          <p className="mb-4 text-xs font-semibold text-slate-500">
            {sessionSource === "backend"
              ? t.backendStatus
              : sessionSource === "fallback"
                ? t.fallbackStatus
                : t.loadingStatus}
          </p>
          {comparison ? (
            <div className="mb-4 w-full rounded-3xl border border-forest-100 bg-white p-4 shadow-card">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-forest-700">{t.sessionMemory}</p>
                <span className="rounded-full bg-forest-50 px-3 py-1 text-xs font-bold text-forest-700">
                  {t.sqlite}
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold text-ink">
                {comparison.hasPrevious ? t.compared : t.baselineStored}
              </p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{comparison.insights[0]}</p>
            </div>
          ) : null}
          <PhoneDemo trip={trip} locale={locale} />
        </div>
      </section>

      <DocumentationSections locale={locale} />
    </main>
  );
}
