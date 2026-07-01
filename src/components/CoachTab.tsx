"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { fetchCoachChat, fetchCoachReport, fetchCoachingTargets, fetchMemoryAwareCoaching, fetchTargetCompletion } from "@/lib/apiClient";
import { generateMockCoachReport } from "@/lib/coachReport";
import type { Locale } from "@/lib/i18n";
import { sourceLabel } from "@/lib/i18n";
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

type StoredCoachChat = {
  messages: CoachChatMessage[];
  chatResponse: CoachChatResponse | null;
};

const copy: Record<
  Locale,
  {
    questions: string[];
    summaryEyebrow: string;
    summaryTitle: string;
    mainFocus: string;
    defaultFocus: string;
    defaultWhy: string;
    defaultPolicy: string;
    evidenceEyebrow: string;
    evidenceTitle: string;
    events: string;
    targetEyebrow: string;
    fallbackTarget: string;
    previousTarget: string;
    completed: string;
    continueFocus: string;
    current: string;
    target: string;
    targetEmpty: string;
    chatEyebrow: string;
    chatTitle: string;
    chatEmpty: string;
    answerEvidence: string;
    placeholder: string;
    ask: string;
    trustTitle: string;
    trustBody: string;
    checksPassed: string;
    needsReview: string;
    knowledge: string;
    memory: string;
    localFallbackPrefix: string;
    localFallbackSafety: string;
  }
> = {
  en: {
    questions: ["Did I improve from last drive?", "Why was this event important?", "What should I focus on next drive?"],
    summaryEyebrow: "AI coach summary",
    summaryTitle: "Post-drive coaching summary",
    mainFocus: "Main focus",
    defaultFocus: "Keep the next drive focused on smoother speed, braking, and steering transitions.",
    defaultWhy: "Smoother speed choice, braking, and steering improve comfort, stability, and predictability.",
    defaultPolicy:
      "Metrics and Risk Events are calculated deterministically. The AI coach explains the evidence and turns it into practical guidance.",
    evidenceEyebrow: "Key evidence",
    evidenceTitle: "What the coach used",
    events: "events",
    targetEyebrow: "Next drive target",
    fallbackTarget: "Keep collecting comparable route reviews",
    previousTarget: "Previous target",
    completed: "Completed",
    continueFocus: "Continue focus",
    current: "Current",
    target: "Target",
    targetEmpty: "Generate another backend session to start measurable target tracking.",
    chatEyebrow: "Ask DriveCoach",
    chatTitle: "Follow up on this drive",
    chatEmpty: "Ask about the main focus, route evidence, or what to improve next time.",
    answerEvidence: "Answer evidence",
    placeholder: "Ask about this drive...",
    ask: "Ask",
    trustTitle: "Evidence & trust",
    trustBody: "Technical grounding is available for review, but hidden by default to keep the coaching flow focused.",
    checksPassed: "Checks passed",
    needsReview: "Needs review",
    knowledge: "Retrieved knowledge",
    memory: "Memory comparison",
    localFallbackPrefix: "For this follow-up, start from deterministic event evidence and focus on one practical improvement:",
    localFallbackSafety: "Local fallback response. Backend coach chat was unavailable.",
  },
  zh: {
    questions: ["和上一次相比有进步吗？", "为什么这个 Risk Event 重要？", "下一次驾驶应该重点关注什么？"],
    summaryEyebrow: "AI 教练总结",
    summaryTitle: "本次行程 coaching summary",
    mainFocus: "主要关注点",
    defaultFocus: "下一次驾驶可以重点关注更平顺的速度、制动和转向过渡。",
    defaultWhy: "更平顺的速度选择、制动和转向有助于提升舒适性、稳定性和可预测性。",
    defaultPolicy:
      "Metrics 和 Risk Events 由 deterministic analysis 计算。AI coach 负责解释 evidence，并把它转化为 practical guidance。",
    evidenceEyebrow: "关键证据",
    evidenceTitle: "Coach 使用的证据",
    events: "个事件",
    targetEyebrow: "下一次驾驶目标",
    fallbackTarget: "继续收集可对比的路线复盘",
    previousTarget: "上一次目标",
    completed: "已完成",
    continueFocus: "继续关注",
    current: "当前",
    target: "目标",
    targetEmpty: "生成下一次后端 session 后，可以开始追踪可衡量目标。",
    chatEyebrow: "询问 DriveCoach",
    chatTitle: "继续追问本次行程",
    chatEmpty: "可以询问主要关注点、路线证据，或下一次驾驶应该如何改进。",
    answerEvidence: "回答依据",
    placeholder: "询问本次驾驶...",
    ask: "发送",
    trustTitle: "证据与可信度",
    trustBody: "技术证据可以展开查看；默认收起是为了让 coaching flow 更聚焦。",
    checksPassed: "检查通过",
    needsReview: "需要复核",
    knowledge: "检索到的知识",
    memory: "历史对比",
    localFallbackPrefix: "这次追问会先基于确定性的事件证据，并聚焦一个可执行的改进点：",
    localFallbackSafety: "本地备用回答。后端 coach chat 当前不可用。",
  },
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
    return stored ? (JSON.parse(stored) as StoredCoachChat) : { messages: [], chatResponse: null };
  } catch {
    return { messages: [], chatResponse: null };
  }
}

function saveStoredChat(tripId: string, value: StoredCoachChat) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(chatStorageKey(tripId), JSON.stringify(value));
  }
}

function formatKnowledgeSource(source?: string) {
  if (!source) return "local knowledge";
  if (source === "internal_product_policy") return "product policy";
  if (source === "supplied_route_reference_image") return "route reference";
  if (source.includes("gov.uk")) return "GOV.UK Highway Code";
  return source;
}

function formatValue(value: number) {
  return value.toFixed(Number.isInteger(value) ? 0 : 1);
}

function fallbackTargets(trip: SampleTrip): CoachingTargetsResponse {
  const brakingEvents = trip.events.filter((event) => event.type.includes("braking")).length;
  const target: CoachingTarget = {
    id: "local-smooth-next-drive",
    title: brakingEvents ? "Reduce late or harsh braking" : "Improve overall smoothness score",
    category: brakingEvents ? "behaviour" : "measurable_score",
    priority: brakingEvents ? "medium" : "low",
    baselineValue: brakingEvents || Math.round(trip.metrics.overallDrivingScore),
    targetValue: brakingEvents ? Math.max(0, brakingEvents - 1) : Math.min(100, Math.round(trip.metrics.overallDrivingScore) + 5),
    unit: brakingEvents ? "events" : "score",
    measurement: brakingEvents
      ? "Count braking-related events and review peak longitudinal deceleration."
      : "Overall driving score from deterministic metrics and Risk Event penalties.",
    whyItMatters: "A measurable target keeps the next drive focused on observable change.",
    nextAction: brakingEvents
      ? "Begin reducing speed earlier before similar bends or junction approaches."
      : "Keep speed, braking, and steering transitions smooth across comparable route sections.",
    evidence: [`Risk events: ${trip.metrics.riskEventCount}`],
    routeContext: [`${trip.route.origin} to ${trip.route.destination}`],
    status: "active",
  };

  return {
    generatedAt: new Date().toISOString(),
    sessionId: trip.id,
    agentMode: "frontend_local_targets_fallback",
    evidencePolicy: "Targets are calculated from deterministic metrics and Risk Events.",
    hasHistory: false,
    targets: [target],
  };
}

function localChatFallback(question: string, report: CoachReport, locale: Locale): CoachChatResponse {
  const t = copy[locale];
  return {
    answer: `${report.summary} ${t.localFallbackPrefix} ${question}`,
    evidenceUsed: [
      { type: "metric", label: "Risk Events", value: `${report.keyFindings.length} report findings` },
      { type: "knowledge", label: "Evidence-first coaching", value: "local fallback" },
    ],
    coachingActions: report.nextSessionFocus.slice(0, 3),
    confidence: "medium",
    safetyNotes: [t.localFallbackSafety],
    followUpQuestions: t.questions,
    agentMode: "frontend_local_chat_fallback",
  };
}

function primaryTarget(completion: TargetCompletionResponse | null, targets: CoachingTargetsResponse | null): CoachingTarget | null {
  return completion?.activeTargets?.[0] ?? targets?.targets?.[0] ?? null;
}

export function CoachTab({ trip, locale }: { trip: SampleTrip; locale: Locale }) {
  const t = copy[locale];
  const [report, setReport] = useState<CoachReport>(() => generateMockCoachReport(trip));
  const [reportSource, setReportSource] = useState<"loading" | "backend" | "fallback">("loading");
  const [targetsResponse, setTargetsResponse] = useState<CoachingTargetsResponse | null>(() => fallbackTargets(trip));
  const [targetsStatus, setTargetsStatus] = useState<"loading" | "backend" | "fallback">("loading");
  const [targetCompletion, setTargetCompletion] = useState<TargetCompletionResponse | null>(() => generateLocalTargetCompletionFallback(trip));
  const [memoryResponse, setMemoryResponse] = useState<MemoryAwareCoachingResponse | null>(() => generateLocalMemoryAwareFallback(trip));
  const [messages, setMessages] = useState<CoachChatMessage[]>([]);
  const [chatResponse, setChatResponse] = useState<CoachChatResponse | null>(null);
  const [draft, setDraft] = useState("");
  const [chatStatus, setChatStatus] = useState<"idle" | "loading">("idle");
  const selectedEvent = trip.events[0];

  const reportSourceLabel = report.agentMode?.startsWith("deepseek_llm")
    ? "DeepSeek"
    : reportSource === "backend"
      ? locale === "zh"
        ? "Agent 工作流"
        : "Agent workflow"
      : reportSource === "fallback"
        ? locale === "zh"
          ? "本地备用"
          : "Local fallback"
        : sourceLabel("loading", locale);

  const chatSourceLabel = useMemo(() => {
    if (!chatResponse) return sourceLabel("ready", locale);
    if (chatResponse.agentMode?.startsWith("deepseek_llm")) return "DeepSeek";
    if (chatResponse.agentMode?.includes("fallback")) return sourceLabel("fallback", locale);
    return "Agent";
  }, [chatResponse, locale]);

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
        if (error instanceof DOMException && error.name === "AbortError") return;
        coachReportCache.set(trip.id, { report: fallbackReport, source: "fallback" });
        setReport(fallbackReport);
        setReportSource("fallback");
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
    const fallback = fallbackTargets(trip);
    setTargetsResponse(fallback);
    setTargetsStatus("loading");

    fetchCoachingTargets(trip, true, controller.signal)
      .then((backendTargets) => {
        coachingTargetsCache.set(trip.id, { targets: backendTargets, source: "backend" });
        setTargetsResponse(backendTargets);
        setTargetsStatus("backend");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        coachingTargetsCache.set(trip.id, { targets: fallback, source: "fallback" });
        setTargetsResponse(fallback);
        setTargetsStatus("fallback");
      });

    return () => controller.abort();
  }, [trip]);

  useEffect(() => {
    const cached = targetCompletionCache.get(trip.id);
    if (cached) {
      setTargetCompletion(cached.completion);
      return;
    }

    const controller = new AbortController();
    const fallback = generateLocalTargetCompletionFallback(trip);
    setTargetCompletion(fallback);

    fetchTargetCompletion(trip, controller.signal)
      .then((backendCompletion) => {
        targetCompletionCache.set(trip.id, { completion: backendCompletion, source: "backend" });
        setTargetCompletion(backendCompletion);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        targetCompletionCache.set(trip.id, { completion: fallback, source: "fallback" });
        setTargetCompletion(fallback);
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
    const fallback = generateLocalMemoryAwareFallback(trip);
    setMemoryResponse(fallback);

    fetchMemoryAwareCoaching(trip, 5, controller.signal)
      .then((backendMemory) => {
        memoryAwareCache.set(trip.id, { memory: backendMemory, source: "backend" });
        setMemoryResponse(backendMemory);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        memoryAwareCache.set(trip.id, { memory: fallback, source: "fallback" });
        setMemoryResponse(fallback);
      });

    return () => controller.abort();
  }, [trip]);

  useEffect(() => {
    const stored = loadStoredChat(trip.id);
    setMessages(Array.isArray(stored.messages) ? stored.messages : []);
    setChatResponse(stored.chatResponse ?? null);
    setDraft("");
  }, [trip.id]);

  const askDriveCoach = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || chatStatus === "loading") return;

    const nextMessages: CoachChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    saveStoredChat(trip.id, { messages: nextMessages, chatResponse });
    setDraft("");
    setChatStatus("loading");

    try {
      const response = await fetchCoachChat({ trip, messages: nextMessages, selectedEvent });
      const completedMessages = [...nextMessages, { role: "assistant" as const, content: response.answer }];
      setChatResponse(response);
      setMessages(completedMessages);
      saveStoredChat(trip.id, { messages: completedMessages, chatResponse: response });
    } catch {
      const fallback = localChatFallback(trimmed, report, locale);
      const completedMessages = [...nextMessages, { role: "assistant" as const, content: fallback.answer }];
      setChatResponse(fallback);
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
  const mainFocus = structured?.mainBehaviouralPattern ?? report.eventSuggestions?.[0]?.suggestion ?? report.behaviourInsight ?? t.defaultFocus;
  const target = primaryTarget(targetCompletion, targetsResponse);
  const firstCompletion = targetCompletion?.results?.[0] ?? null;
  const evidenceItems = report.evidenceUsed?.length
    ? report.evidenceUsed.slice(0, 3)
    : report.keyFindings.slice(0, 3).map((finding) => ({ type: "finding", label: finding }));

  return (
    <div className="space-y-4">
      <section className="rounded-[32px] bg-ink p-6 text-white shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">{t.summaryEyebrow}</p>
          <span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-100">
            {reportSourceLabel}
          </span>
        </div>
        <h3 className="mt-3 text-2xl font-semibold leading-8">{t.summaryTitle}</h3>
        <p className="mt-3 text-sm leading-6 text-slate-100">{structured?.overallAssessment ?? report.summary}</p>
        <div className="mt-5 border-t border-white/10 pt-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-200">{t.mainFocus}</p>
          <p className="mt-2 text-lg font-semibold leading-7 text-white">{mainFocus}</p>
          <p className="mt-3 text-sm leading-6 text-slate-300">{structured?.whyItMatters ?? t.defaultWhy}</p>
        </div>
        <p className="mt-4 text-xs leading-5 text-slate-300">{report.evidencePolicy ?? t.defaultPolicy}</p>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.evidenceEyebrow}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{t.evidenceTitle}</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
            {trip.events.length} {t.events}
          </span>
        </div>
        <div className="mt-3 grid gap-2">
          {evidenceItems.map((evidence) => (
            <div key={`${evidence.type}-${evidence.label}`} className="rounded-2xl bg-slate-50 px-3 py-2">
              <p className="text-sm font-semibold leading-5 text-ink">{evidence.label}</p>
              {"value" in evidence && evidence.value ? <p className="mt-0.5 text-xs text-slate-500">{String(evidence.value)}</p> : null}
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.targetEyebrow}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{target?.title ?? t.fallbackTarget}</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
            {targetsStatus === "loading" ? sourceLabel("loading", locale) : sourceLabel("active", locale)}
          </span>
        </div>
        {firstCompletion ? (
          <div className="mt-3 rounded-2xl bg-slate-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{t.previousTarget}</p>
            <p className="mt-1 text-sm font-semibold leading-5 text-ink">
              {firstCompletion.completed ? t.completed : t.continueFocus} - {firstCompletion.title}
            </p>
          </div>
        ) : null}
        {target ? (
          <>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <div className="rounded-2xl bg-slate-50 px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">{t.current}</p>
                <p className="mt-1 text-base font-semibold text-ink">
                  {formatValue(target.baselineValue)}
                  <span className="text-xs font-medium text-slate-500"> {target.unit}</span>
                </p>
              </div>
              <div className="rounded-2xl bg-forest-50 px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">{t.target}</p>
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
          <p className="mt-3 text-sm leading-6 text-slate-600">{t.targetEmpty}</p>
        )}
      </section>

      <section className="rounded-[24px] border border-forest-100 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-forest-700">{t.chatEyebrow}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{t.chatTitle}</h3>
          </div>
          <span className="rounded-full bg-forest-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-forest-700">
            {chatStatus === "loading" ? sourceLabel("thinking", locale) : chatSourceLabel}
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
          <div className="mt-4 rounded-2xl bg-forest-50 p-3 text-sm leading-5 text-forest-800">{t.chatEmpty}</div>
        )}

        {chatResponse ? (
          <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{t.answerEvidence}</p>
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
          {(chatResponse?.followUpQuestions ?? t.questions).slice(0, 3).map((question) => (
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
            placeholder={t.placeholder}
            className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-forest-400"
          />
          <button
            type="submit"
            disabled={chatStatus === "loading" || !draft.trim()}
            className="rounded-2xl bg-forest-700 px-4 py-2 text-sm font-bold text-white transition hover:bg-forest-600 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {t.ask}
          </button>
        </form>
      </section>

      <details className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-ink">{t.trustTitle}</summary>
        <p className="mt-3 text-xs leading-5 text-slate-500">{t.trustBody}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {report.evaluation ? (
            <>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                Eval {report.evaluation.qualityScore}/100
              </span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                {report.evaluation.passed ? t.checksPassed : t.needsReview}
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
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.knowledge}</p>
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
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{t.memory}</p>
            <p className="mt-1 text-xs leading-5 text-slate-600">{memoryResponse.memorySummary}</p>
          </div>
        ) : null}
      </details>
    </div>
  );
}
