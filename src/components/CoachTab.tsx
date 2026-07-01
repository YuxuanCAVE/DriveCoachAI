"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { fetchCoachChat, fetchCoachReport, fetchCoachingTargets, fetchMemoryAwareCoaching, fetchTargetCompletion } from "@/lib/apiClient";
import { generateMockCoachReport } from "@/lib/coachReport";
import { generateLocalMemoryAwareFallback } from "@/lib/memoryAwareFallback";
import { coachReportCache, coachingTargetsCache, memoryAwareCache, targetCompletionCache } from "@/lib/sessionResultCache";
import { generateLocalTargetCompletionFallback } from "@/lib/targetCompletionFallback";
import type {
  CoachChatMessage,
  CoachChatResponse,
  CoachReport,
  CoachingTarget,
  CoachingTargetsResponse,
  MemoryAwareCoachingResponse,
  SampleTrip,
  TargetCompletionResponse,
} from "@/types/driving";

const recommendedQuestions = [
  "Did I improve from last drive?",
  "Why was this event risky?",
  "What should I focus on next drive?",
];

type StoredCoachChat = {
  messages: CoachChatMessage[];
  chatResponse: CoachChatResponse | null;
};

function chatStorageKey(tripId: string) {
  return `drivecoach-chat:${tripId}`;
}

function loadStoredChat(tripId: string): StoredCoachChat {
  if (typeof window === "undefined") {
    return { messages: [], chatResponse: null };
  }

  try {
    const stored = window.localStorage.getItem(chatStorageKey(tripId));
    if (!stored) {
      return { messages: [], chatResponse: null };
    }
    const parsed = JSON.parse(stored) as StoredCoachChat;
    return {
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
      chatResponse: parsed.chatResponse ?? null,
    };
  } catch {
    return { messages: [], chatResponse: null };
  }
}

function saveStoredChat(tripId: string, value: StoredCoachChat) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(chatStorageKey(tripId), JSON.stringify(value));
}

function localChatFallback(question: string, report: CoachReport): CoachChatResponse {
  return {
    answer: `${report.summary} For this follow-up, start from the deterministic event evidence and focus on one practical improvement at a time: ${question}`,
    evidenceUsed: [
      { type: "metric", label: "Risk events", value: `${report.keyFindings.length} report findings` },
      { type: "knowledge", label: "Evidence-first coaching", value: "local fallback" },
    ],
    coachingActions: report.nextSessionFocus.slice(0, 3),
    confidence: "medium",
    safetyNotes: ["Local fallback response. Backend coach chat was unavailable."],
    followUpQuestions: recommendedQuestions,
    agentMode: "frontend_local_chat_fallback",
  };
}

function localCoachingTargetsFallback(trip: SampleTrip): CoachingTargetsResponse {
  const hasBraking = trip.events.some((event) => event.type === "late_braking_before_curve" || event.type === "harsh_braking");
  const hasLateral = trip.events.some(
    (event) => event.type === "high_lateral_acceleration" || event.type === "unstable_cornering" || event.type === "high_speed_in_curve",
  );
  const targets = [
    hasBraking
      ? {
          id: "local-reduce-late-braking",
          title: "Reduce late or harsh braking",
          category: "behaviour",
          priority: "medium" as const,
          baselineValue: trip.events.filter((event) => event.type === "late_braking_before_curve" || event.type === "harsh_braking").length,
          targetValue: 0,
          unit: "events",
          measurement: "Count braking-related events and review peak longitudinal deceleration.",
          whyItMatters: "Earlier braking improves comfort and predictability before higher-demand route sections.",
          nextAction: "Begin reducing speed earlier before similar bends or junction approaches.",
          evidence: [`Peak longitudinal acceleration: ${trip.metrics.maxAbsAx.toFixed(1)} m/s^2`],
          routeContext: [trip.route.name],
          status: "active",
        }
      : null,
    hasLateral
      ? {
          id: "local-lower-cornering-demand",
          title: "Lower peak cornering demand",
          category: "route_context",
          priority: "medium" as const,
          baselineValue: Number(trip.metrics.maxAbsAy.toFixed(1)),
          targetValue: Math.max(1.8, Number((trip.metrics.maxAbsAy - 0.3).toFixed(1))),
          unit: "m/s^2",
          measurement: "Maximum absolute lateral acceleration on curve and junction-context sections.",
          whyItMatters: "Lower lateral demand supports smoother cornering and more predictable steering response.",
          nextAction: "Settle speed before entering higher-curvature sections.",
          evidence: [`Lateral stability score: ${Math.round(trip.metrics.lateralStabilityScore)}/100`],
          routeContext: [trip.route.name],
          status: "active",
        }
      : null,
    {
      id: "local-improve-overall-smoothness",
      title: "Improve overall smoothness score",
      category: "measurable_score",
      priority: "low" as const,
      baselineValue: Math.round(trip.metrics.overallDrivingScore),
      targetValue: Math.min(100, Math.round(trip.metrics.overallDrivingScore) + 5),
      unit: "score",
      measurement: "Overall driving score from deterministic metrics and risk-event penalties.",
      whyItMatters: "A score target keeps the next drive focused on measurable change.",
      nextAction: "Review the highest-priority event first, then compare the next session against this baseline.",
      evidence: [`Risk events: ${trip.metrics.riskEventCount}`],
      routeContext: [`${trip.route.origin} to ${trip.route.destination}`],
      status: "active",
    },
  ].filter(Boolean);

  return {
    generatedAt: new Date().toISOString(),
    sessionId: trip.id,
    agentMode: "frontend_local_targets_fallback",
    evidencePolicy:
      "Targets are calculated from deterministic metrics and risk events. The AI coach can explain them, but the measurement criteria remain explicit.",
    hasHistory: false,
    targets: targets.slice(0, 3) as CoachingTargetsResponse["targets"],
  };
}

function formatKnowledgeSource(source?: string) {
  if (!source) {
    return "local knowledge";
  }
  if (source === "internal_product_policy") {
    return "product policy";
  }
  if (source === "supplied_route_reference_image") {
    return "route reference";
  }
  if (source.includes("gov.uk")) {
    return "GOV.UK Highway Code";
  }
  return source;
}

function primaryTarget(completion: TargetCompletionResponse | null, targets: CoachingTargetsResponse | null): CoachingTarget | null {
  return completion?.activeTargets?.[0] ?? targets?.targets?.[0] ?? null;
}

function formatValue(value: number) {
  return value.toFixed(Number.isInteger(value) ? 0 : 1);
}

export function CoachTab({ trip }: { trip: SampleTrip }) {
  const [report, setReport] = useState<CoachReport>(() => generateMockCoachReport(trip));
  const [reportSource, setReportSource] = useState<"loading" | "backend" | "fallback">("loading");
  const [targetsResponse, setTargetsResponse] = useState<CoachingTargetsResponse | null>(() => localCoachingTargetsFallback(trip));
  const [targetsStatus, setTargetsStatus] = useState<"loading" | "backend" | "fallback">("loading");
  const [targetCompletion, setTargetCompletion] = useState<TargetCompletionResponse | null>(() =>
    generateLocalTargetCompletionFallback(trip),
  );
  const [targetCompletionStatus, setTargetCompletionStatus] = useState<"loading" | "backend" | "fallback">("loading");
  const [memoryResponse, setMemoryResponse] = useState<MemoryAwareCoachingResponse | null>(() => generateLocalMemoryAwareFallback(trip));
  const [messages, setMessages] = useState<CoachChatMessage[]>([]);
  const [chatResponse, setChatResponse] = useState<CoachChatResponse | null>(null);
  const [draft, setDraft] = useState("");
  const [chatStatus, setChatStatus] = useState<"idle" | "loading">("idle");
  const selectedEvent = trip.events[0];

  const sourceLabel = report.agentMode?.startsWith("deepseek_llm")
    ? "DeepSeek"
    : reportSource === "backend"
      ? "Agent workflow"
      : reportSource === "fallback"
        ? "Local fallback"
        : "Loading";

  const chatSourceLabel = useMemo(() => {
    if (!chatResponse) {
      return "Ready";
    }
    if (chatResponse.agentMode?.startsWith("deepseek_llm")) {
      return "DeepSeek";
    }
    if (chatResponse.agentMode?.includes("fallback")) {
      return "Fallback";
    }
    return "Agent";
  }, [chatResponse]);

  useEffect(() => {
    const cached = coachReportCache.get(trip.id);
    if (cached) {
      setReport(cached.report);
      setReportSource(cached.source);
      return;
    }

    const controller = new AbortController();
    const fallbackReport = generateMockCoachReport(trip);
    setReport(fallbackReport);
    setReportSource("loading");

    fetchCoachReport(trip, controller.signal)
      .then((backendReport) => {
        coachReportCache.set(trip.id, { report: backendReport, source: "backend" });
        setReport(backendReport);
        setReportSource("backend");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        coachReportCache.set(trip.id, { report: fallbackReport, source: "fallback" });
        setReport(fallbackReport);
        setReportSource("fallback");
      });

    return () => controller.abort();
  }, [trip]);

  useEffect(() => {
    const cached = memoryAwareCache.get(trip.id);
    if (cached) {
      setMemoryResponse(cached.memory);
      return;
    }

    const controller = new AbortController();
    const fallbackMemory = generateLocalMemoryAwareFallback(trip);
    setMemoryResponse(fallbackMemory);

    fetchMemoryAwareCoaching(trip, 5, controller.signal)
      .then((backendMemory) => {
        memoryAwareCache.set(trip.id, { memory: backendMemory, source: "backend" });
        setMemoryResponse(backendMemory);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        memoryAwareCache.set(trip.id, { memory: fallbackMemory, source: "fallback" });
        setMemoryResponse(fallbackMemory);
      });

    return () => controller.abort();
  }, [trip]);

  useEffect(() => {
    const cached = coachingTargetsCache.get(trip.id);
    if (cached) {
      setTargetsResponse(cached.targets);
      setTargetsStatus(cached.source);
      return;
    }

    const controller = new AbortController();
    const fallbackTargets = localCoachingTargetsFallback(trip);
    setTargetsResponse(fallbackTargets);
    setTargetsStatus("loading");

    fetchCoachingTargets(trip, true, controller.signal)
      .then((backendTargets) => {
        coachingTargetsCache.set(trip.id, { targets: backendTargets, source: "backend" });
        setTargetsResponse(backendTargets);
        setTargetsStatus("backend");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        coachingTargetsCache.set(trip.id, { targets: fallbackTargets, source: "fallback" });
        setTargetsResponse(fallbackTargets);
        setTargetsStatus("fallback");
      });

    return () => controller.abort();
  }, [trip]);

  useEffect(() => {
    const cached = targetCompletionCache.get(trip.id);
    if (cached) {
      setTargetCompletion(cached.completion);
      setTargetCompletionStatus(cached.source);
      return;
    }

    const controller = new AbortController();
    const fallbackCompletion = generateLocalTargetCompletionFallback(trip);
    setTargetCompletion(fallbackCompletion);
    setTargetCompletionStatus("loading");

    fetchTargetCompletion(trip, controller.signal)
      .then((backendCompletion) => {
        targetCompletionCache.set(trip.id, { completion: backendCompletion, source: "backend" });
        setTargetCompletion(backendCompletion);
        setTargetCompletionStatus("backend");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        targetCompletionCache.set(trip.id, { completion: fallbackCompletion, source: "fallback" });
        setTargetCompletion(fallbackCompletion);
        setTargetCompletionStatus("fallback");
      });

    return () => controller.abort();
  }, [trip]);

  useEffect(() => {
    const stored = loadStoredChat(trip.id);
    setMessages(stored.messages);
    setChatResponse(stored.chatResponse);
    setDraft("");
  }, [trip.id]);

  const askDriveCoach = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || chatStatus === "loading") {
      return;
    }

    const nextMessages: CoachChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    saveStoredChat(trip.id, { messages: nextMessages, chatResponse });
    setDraft("");
    setChatStatus("loading");

    try {
      const response = await fetchCoachChat({
        trip,
        messages: nextMessages,
        selectedEvent,
      });
      setChatResponse(response);
      const completedMessages = [...nextMessages, { role: "assistant" as const, content: response.answer }];
      setMessages(completedMessages);
      saveStoredChat(trip.id, { messages: completedMessages, chatResponse: response });
    } catch {
      const fallback = localChatFallback(trimmed, report);
      setChatResponse(fallback);
      const completedMessages = [...nextMessages, { role: "assistant" as const, content: fallback.answer }];
      setMessages(completedMessages);
      saveStoredChat(trip.id, { messages: completedMessages, chatResponse: fallback });
    } finally {
      setChatStatus("idle");
    }
  };

  const submitQuestion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void askDriveCoach(draft);
  };

  const structured = report.structuredSummary;
  const mainFocus =
    structured?.mainBehaviouralPattern ??
    report.eventSuggestions?.[0]?.suggestion ??
    report.behaviourInsight ??
    "Keep the next drive focused on smoother speed, braking, and steering transitions.";
  const target = primaryTarget(targetCompletion, targetsResponse);
  const firstCompletion = targetCompletion?.results?.[0] ?? null;
  const evidenceItems = report.evidenceUsed?.length
    ? report.evidenceUsed.slice(0, 3)
    : report.keyFindings.slice(0, 3).map((finding) => ({ type: "finding", label: finding }));

  return (
    <div className="space-y-4">
      <section className="rounded-[32px] bg-ink p-6 text-white shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">AI coach summary</p>
          <span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-100">
            {sourceLabel}
          </span>
        </div>
        <h3 className="mt-3 text-2xl font-semibold leading-8">Post-drive coaching summary</h3>
        <p className="mt-3 text-sm leading-6 text-slate-100">{structured?.overallAssessment ?? report.summary}</p>
        <div className="mt-5 border-t border-white/10 pt-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-200">Main focus</p>
          <p className="mt-2 text-lg font-semibold leading-7 text-white">{mainFocus}</p>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {structured?.whyItMatters ??
              "Smoother speed choice, braking, and steering improve comfort, stability, and predictability."}
          </p>
        </div>
        <p className="mt-4 text-xs leading-5 text-slate-300">
          {report.evidencePolicy ??
            "Metrics and risk events are calculated deterministically. The AI coach explains the evidence and turns it into practical guidance."}
        </p>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Key evidence</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">What the coach used</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
            {trip.events.length} events
          </span>
        </div>
        <div className="mt-3 grid gap-2">
          {evidenceItems.map((evidence) => (
            <div key={`${evidence.type}-${evidence.label}`} className="rounded-2xl bg-slate-50 px-3 py-2">
              <p className="text-sm font-semibold leading-5 text-ink">{evidence.label}</p>
              {"value" in evidence && evidence.value ? (
                <p className="mt-0.5 text-xs text-slate-500">{String(evidence.value)}</p>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Next drive target</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{target?.title ?? "Keep collecting comparable route reviews"}</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
            {targetsStatus === "loading" || targetCompletionStatus === "loading" ? "Loading" : "Active"}
          </span>
        </div>
        {firstCompletion ? (
          <div className="mt-3 rounded-2xl bg-slate-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Previous target</p>
            <p className="mt-1 text-sm font-semibold leading-5 text-ink">
              {firstCompletion.completed ? "Completed" : "Continue focus"} - {firstCompletion.title}
            </p>
          </div>
        ) : null}
        {target ? (
          <>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <div className="rounded-2xl bg-slate-50 px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Current</p>
                <p className="mt-1 text-base font-semibold text-ink">
                  {formatValue(target.baselineValue)}
                  <span className="text-xs font-medium text-slate-500"> {target.unit}</span>
                </p>
              </div>
              <div className="rounded-2xl bg-forest-50 px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">Target</p>
                <p className="mt-1 text-base font-semibold text-forest-800">
                  {formatValue(target.targetValue)}
                  <span className="text-xs font-medium text-slate-500"> {target.unit}</span>
                </p>
              </div>
            </div>
            <p className="mt-3 text-sm font-semibold leading-5 text-forest-800">{target.nextAction}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">{target.measurement}</p>
          </>
        ) : (
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Generate another backend session to start measurable target tracking.
          </p>
        )}
      </section>

      <section className="rounded-[24px] border border-forest-100 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">Ask DriveCoach</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">Follow up on this drive</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
            {chatStatus === "loading" ? "Thinking" : chatSourceLabel}
          </span>
        </div>

        {messages.length > 0 ? (
          <div className="mt-4 max-h-64 space-y-2 overflow-y-auto pr-1">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}-${message.content}`}
                className={`rounded-2xl px-3 py-2 text-sm leading-5 ${
                  message.role === "user" ? "ml-8 bg-forest-700 text-white" : "mr-6 bg-slate-50 text-slate-700"
                }`}
              >
                {message.content}
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">
            Ask about the main focus, route evidence, or what to improve next time.
          </div>
        )}

        {chatResponse ? (
          <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Answer evidence</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {chatResponse.evidenceUsed.slice(0, 3).map((evidence) => (
                <span key={`${evidence.type}-${evidence.label}`} className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                  {evidence.label}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-4 flex flex-wrap gap-2">
          {(chatResponse?.followUpQuestions ?? recommendedQuestions).slice(0, 3).map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => void askDriveCoach(question)}
              disabled={chatStatus === "loading"}
              className="rounded-full border border-forest-100 bg-white px-3 py-1.5 text-xs font-semibold text-forest-700 shadow-sm transition hover:border-forest-300 disabled:cursor-wait disabled:opacity-60"
            >
              {question}
            </button>
          ))}
        </div>

        <form onSubmit={submitQuestion} className="mt-4 flex gap-2">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask about this drive..."
            className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-forest-400"
          />
          <button
            type="submit"
            disabled={chatStatus === "loading" || !draft.trim()}
            className="rounded-2xl bg-forest-700 px-4 py-2 text-sm font-bold text-white transition hover:bg-forest-600 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Ask
          </button>
        </form>
      </section>

      <details className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-ink">Evidence & trust</summary>
        <p className="mt-3 text-xs leading-5 text-slate-500">
          Technical grounding is available for review, but hidden by default to keep the coaching flow focused.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {report.evaluation ? (
            <>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                Eval {report.evaluation.qualityScore}/100
              </span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                {report.evaluation.passed ? "Checks passed" : "Needs review"}
              </span>
            </>
          ) : null}
          {report.workflowEngine ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
              {report.workflowEngine}
            </span>
          ) : null}
          {report.trace?.traceId ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
              Trace #{report.trace.traceId}
            </span>
          ) : null}
        </div>
        {report.retrievedKnowledge?.length ? (
          <div className="mt-4 grid gap-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Retrieved knowledge</p>
            {report.retrievedKnowledge.slice(0, 4).map((knowledge) => (
              <div key={knowledge.id} className="rounded-2xl border border-slate-100 bg-slate-50 px-3 py-2">
                <p className="text-xs font-semibold text-ink">{knowledge.title}</p>
                <p className="mt-0.5 text-[11px] font-medium text-slate-500">{formatKnowledgeSource(knowledge.source)}</p>
                {knowledge.whyUsed ? <p className="mt-1 text-[11px] leading-4 text-slate-600">{knowledge.whyUsed}</p> : null}
              </div>
            ))}
          </div>
        ) : null}
        {memoryResponse ? (
          <div className="mt-4 rounded-2xl bg-slate-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Memory comparison</p>
            <p className="mt-1 text-xs leading-5 text-slate-600">{memoryResponse.memorySummary}</p>
          </div>
        ) : null}
      </details>
    </div>
  );
}
