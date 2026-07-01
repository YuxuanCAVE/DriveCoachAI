import type { Locale } from "@/lib/i18n";

type SectionCopy = {
  productPainPoints: string[];
  journeySteps: string[];
  architectureItems: { title: string; body: string }[];
  agentItems: string[];
  evaluationItems: { title: string; body: string }[];
  roadmapItems: { phase: string; title: string; body: string }[];
  sections: {
    product: { eyebrow: string; title: string; body: string; painTitle: string; journeyTitle: string };
    architecture: { eyebrow: string; title: string; body: string; diagram: string[] };
    agent: { eyebrow: string; title: string; body: string; nodeLabel: string };
    evaluation: { eyebrow: string; title: string; body: string; boundaryTitle: string; boundaryBody: string };
    roadmap: { eyebrow: string; title: string; body: string };
  };
};

const copy: Record<Locale, SectionCopy> = {
  en: {
    productPainPoints: [
      "Raw vehicle telemetry is accurate but difficult to interpret as coaching feedback.",
      "Risk Events need route context, not only timestamps and signal peaks.",
      "AI advice must explain deterministic evidence instead of repeating generic driving tips.",
    ],
    journeySteps: [
      "Trip auto-captured or demo generated",
      "Vehicle behaviour analysed",
      "Route-aware Risk Events detected",
      "AI coach explains evidence",
      "Next-drive target and history updated",
    ],
    architectureItems: [
      {
        title: "Frontend",
        body: "Next.js product demo with Summary, Drive Data, Coach, and History inside an iPhone-style review surface.",
      },
      {
        title: "Backend",
        body: "FastAPI endpoints generate demo sessions, analyse telemetry, run coach reports, manage memory, and expose evaluation results.",
      },
      {
        title: "Analytics",
        body: "Deterministic metrics and context-aware event detection calculate the evidence before any AI language generation.",
      },
      {
        title: "Memory",
        body: "SQLite stores compact recent sessions for score trends, previous-drive comparison, and target completion.",
      },
    ],
    agentItems: [
      "LoadTripNode collects trip, route, metrics, events, and optional memory context.",
      "AnalyseEvidenceNode identifies the main behavioural pattern and top evidence.",
      "RetrieveKnowledgeNode selects RAG-lite snippets by event type, route context, and user question.",
      "GenerateCoachReportNode creates the coaching summary using DeepSeek when configured, or deterministic fallback.",
      "ValidateReportNode checks route relevance, evidence use, specificity, measurability, and overclaim control.",
      "ReviseReportNode repairs missing context or unsafe language before returning the structured report.",
    ],
    evaluationItems: [
      {
        title: "Driving metrics",
        body: "Scores combine longitudinal smoothness, lateral stability, event burden, and context adaptation.",
      },
      {
        title: "Context thresholds",
        body: "Risk rules adjust by road context, target speed, curvature, traffic complexity, and lateral demand.",
      },
      {
        title: "Agent quality",
        body: "Reports are evaluated for evidence coverage, route-context relevance, suggestion specificity, measurable targets, and no medical overclaiming.",
      },
    ],
    roadmapItems: [
      {
        phase: "Now",
        title: "Portfolio-grade MVP",
        body: "Single-page demo, FastAPI bridge, deterministic analysis, AI coach, RAG-lite, memory, and documentation.",
      },
      {
        phase: "Next",
        title: "In-page documentation and bilingual experience",
        body: "Make the web app explain the product story and support English / Chinese presentation paths.",
      },
      {
        phase: "Later",
        title: "Real data and calibrated evaluation",
        body: "Add real/simulator telemetry, threshold calibration, ADAS-on/off comparison, and stronger retrieval infrastructure.",
      },
    ],
    sections: {
      product: {
        eyebrow: "Product",
        title: "A post-drive coaching product, not a raw telemetry dashboard.",
        body: "DriveCoach AI translates vehicle behaviour, route context, and optional wearable signals into a clear review: what happened, why it matters, and what to focus on next.",
        painTitle: "Core user pain points",
        journeyTitle: "User journey",
      },
      architecture: {
        eyebrow: "Architecture",
        title: "A thin product UI on top of deterministic analysis and an observable agent layer.",
        body: "The frontend stays focused on the product story. The backend owns session generation, analysis, memory, agent workflow, and evaluation so future real telemetry can reuse the same contract.",
        diagram: ["Frontend", "Backend", "Analytics", "Agent", "Memory"],
      },
      agent: {
        eyebrow: "Agent",
        title: "The AI coach is a workflow, not a single prompt.",
        body: "The agent uses deterministic trip evidence, route context, RAG-lite knowledge, optional memory, and validation gates before returning a structured coaching report.",
        nodeLabel: "Node",
      },
      evaluation: {
        eyebrow: "Evaluation",
        title: "Trust comes from separating evidence, interpretation, and quality checks.",
        body: "Driving metrics are calculated before the AI speaks. The report is then evaluated for usefulness, route relevance, measurable guidance, and claim boundaries.",
        boundaryTitle: "Boundary",
        boundaryBody:
          "Current thresholds are transparent coaching heuristics for the demo route. They are not universal safety limits and should be calibrated with labelled real or simulator data before operational use.",
      },
      roadmap: {
        eyebrow: "Roadmap",
        title: "Build the product story first, then add more data and stronger retrieval.",
        body: "The next phases prioritise presentation quality, bilingual access, real-data calibration, and production-grade knowledge retrieval without overcomplicating the current MVP.",
      },
    },
  },
  zh: {
    productPainPoints: [
      "车辆遥测数据很准确，但很难直接转化成驾驶者能理解的 coaching feedback。",
      "Risk Event 不能只看时间戳和信号峰值，还需要结合 route context。",
      "AI 建议必须解释 deterministic evidence，而不是重复泛泛的驾驶建议。",
    ],
    journeySteps: [
      "Trip 自动采集或生成 demo session",
      "分析 vehicle behaviour",
      "检测 route-aware Risk Events",
      "AI coach 解释 evidence",
      "更新 next-drive target 和 history",
    ],
    architectureItems: [
      {
        title: "Frontend",
        body: "Next.js 产品 demo，用 iPhone-style review surface 呈现 Summary、Drive Data、Coach 和 History。",
      },
      {
        title: "Backend",
        body: "FastAPI 负责 demo session 生成、telemetry 分析、coach report、memory 管理和 evaluation 输出。",
      },
      {
        title: "Analytics",
        body: "在 AI 生成语言之前，先用 deterministic metrics 和 context-aware event detection 计算证据。",
      },
      {
        title: "Memory",
        body: "SQLite 保存轻量 session history，用于 score trend、previous-drive comparison 和 target completion。",
      },
    ],
    agentItems: [
      "LoadTripNode 收集 trip、route、metrics、events 和 optional memory context。",
      "AnalyseEvidenceNode 识别主要 behavioural pattern 和关键 evidence。",
      "RetrieveKnowledgeNode 按 event type、route context 和用户问题检索 RAG-lite snippets。",
      "GenerateCoachReportNode 在有 DeepSeek 配置时生成 coaching summary，否则使用 deterministic fallback。",
      "ValidateReportNode 检查 route relevance、evidence use、specificity、measurability 和 overclaim control。",
      "ReviseReportNode 修复缺失 context 或不合适语言，再返回 structured report。",
    ],
    evaluationItems: [
      {
        title: "Driving metrics",
        body: "分数综合 longitudinal smoothness、lateral stability、event burden 和 context adaptation。",
      },
      {
        title: "Context thresholds",
        body: "Risk rules 会根据 road context、target speed、curvature、traffic complexity 和 lateral demand 调整。",
      },
      {
        title: "Agent quality",
        body: "Coach report 会检查 evidence coverage、route-context relevance、suggestion specificity、measurable targets 和 no medical overclaiming。",
      },
    ],
    roadmapItems: [
      {
        phase: "Now",
        title: "Portfolio-grade MVP",
        body: "单页 demo、FastAPI bridge、deterministic analysis、AI coach、RAG-lite、memory 和文档体系。",
      },
      {
        phase: "Next",
        title: "页面内文档中心和 bilingual experience",
        body: "让网页直接讲清楚产品故事，并支持中文答辩和英文 GitHub 展示。",
      },
      {
        phase: "Later",
        title: "Real data 和 calibrated evaluation",
        body: "接入真实/仿真 telemetry、threshold calibration、ADAS-on/off comparison 和更强的 retrieval infrastructure。",
      },
    ],
    sections: {
      product: {
        eyebrow: "Product",
        title: "这是 post-drive coaching product，不是原始 telemetry dashboard。",
        body: "DriveCoach AI 把 vehicle behaviour、route context 和 optional wearable signals 转化成清晰的行程复盘：发生了什么、为什么重要、下一次应该关注什么。",
        painTitle: "核心用户痛点",
        journeyTitle: "用户链路",
      },
      architecture: {
        eyebrow: "Architecture",
        title: "轻量产品 UI 之下，是 deterministic analysis 和可观测的 agent layer。",
        body: "Frontend 负责讲清楚产品体验；Backend 负责 session generation、analysis、memory、agent workflow 和 evaluation，方便未来接入真实 telemetry。",
        diagram: ["Frontend", "Backend", "Analytics", "Agent", "Memory"],
      },
      agent: {
        eyebrow: "Agent",
        title: "AI coach 是一个 workflow，不是一个单独 prompt。",
        body: "Agent 会基于 deterministic trip evidence、route context、RAG-lite knowledge、optional memory 和 validation gates，返回 structured coaching report。",
        nodeLabel: "Node",
      },
      evaluation: {
        eyebrow: "Evaluation",
        title: "可信度来自 evidence、interpretation 和 quality checks 的分离。",
        body: "Driving metrics 在 AI 输出之前先计算完成。随后系统会评估 report 的 usefulness、route relevance、measurable guidance 和 claim boundaries。",
        boundaryTitle: "Boundary",
        boundaryBody:
          "当前 thresholds 是面向 demo route 的透明 coaching heuristics，不是通用 safety limits。用于真实场景前，需要用标注后的真实或仿真数据进行 calibration。",
      },
      roadmap: {
        eyebrow: "Roadmap",
        title: "先把产品故事做完整，再逐步增强数据和 retrieval。",
        body: "后续阶段优先提升展示质量、bilingual access、real-data calibration 和 production-grade knowledge retrieval，同时避免让当前 MVP 过度复杂。",
      },
    },
  },
};

function SectionHeader({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="max-w-3xl">
      <p className="text-sm font-bold uppercase tracking-[0.2em] text-forest-700">{eyebrow}</p>
      <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink md:text-4xl">{title}</h2>
      <p className="mt-4 text-base leading-7 text-slate-600">{body}</p>
    </div>
  );
}

function ConnectorDiagram({ items }: { items: string[] }) {
  return (
    <div className="grid gap-3 rounded-[28px] border border-forest-100 bg-white p-4 shadow-card md:grid-cols-5">
      {items.map((item, index) => (
        <div key={item} className="relative rounded-3xl border border-slate-200 bg-forest-50/50 p-4">
          <span className="text-xs font-bold uppercase tracking-[0.16em] text-forest-700">
            {String(index + 1).padStart(2, "0")}
          </span>
          <p className="mt-3 text-sm font-bold text-ink">{item}</p>
          {index < items.length - 1 ? (
            <span className="absolute -right-3 top-1/2 hidden h-px w-6 bg-forest-600 md:block" />
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function DocumentationSections({ locale }: { locale: Locale }) {
  const t = copy[locale];

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-6 pb-24">
      <section id="product" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader {...t.sections.product} />

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[28px] border border-slate-200 bg-white p-5">
            <h3 className="text-lg font-semibold text-ink">{t.sections.product.painTitle}</h3>
            <div className="mt-5 space-y-3">
              {t.productPainPoints.map((point) => (
                <div key={point} className="flex gap-3 rounded-2xl bg-slate-50 p-3">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-forest-700" />
                  <p className="text-sm leading-6 text-slate-600">{point}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-forest-100 bg-forest-50 p-5">
            <h3 className="text-lg font-semibold text-ink">{t.sections.product.journeyTitle}</h3>
            <div className="mt-5 space-y-3">
              {t.journeySteps.map((step, index) => (
                <div key={step} className="flex items-center gap-3">
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-forest-700 text-xs font-bold text-white">
                    {index + 1}
                  </span>
                  <p className="text-sm font-semibold text-ink">{step}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="architecture" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader {...t.sections.architecture} />

        <div className="mt-8">
          <ConnectorDiagram items={t.sections.architecture.diagram} />
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {t.architectureItems.map((item) => (
            <article key={item.title} className="rounded-[26px] border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-ink">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="agent" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader {...t.sections.agent} />

        <div className="mt-8 grid gap-3">
          {t.agentItems.map((item, index) => (
            <div key={item} className="grid gap-3 rounded-3xl border border-slate-200 bg-white p-4 md:grid-cols-[120px_1fr] md:items-center">
              <span className="text-xs font-bold uppercase tracking-[0.18em] text-forest-700">
                {t.sections.agent.nodeLabel} {index + 1}
              </span>
              <p className="text-sm leading-6 text-slate-600">{item}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="evaluation" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader {...t.sections.evaluation} />

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {t.evaluationItems.map((item) => (
            <article key={item.title} className="rounded-[28px] border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-ink">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.body}</p>
            </article>
          ))}
        </div>

        <div className="mt-5 rounded-[28px] border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-amber-800">{t.sections.evaluation.boundaryTitle}</p>
          <p className="mt-2 text-sm leading-6 text-amber-900">{t.sections.evaluation.boundaryBody}</p>
        </div>
      </section>

      <section id="roadmap" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader {...t.sections.roadmap} />

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {t.roadmapItems.map((item) => (
            <article key={item.title} className="rounded-[28px] border border-slate-200 bg-white p-5">
              <span className="rounded-full bg-forest-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.14em] text-forest-700">
                {item.phase}
              </span>
              <h3 className="mt-4 text-lg font-semibold text-ink">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.body}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
