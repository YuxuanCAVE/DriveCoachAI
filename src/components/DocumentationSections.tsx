const productPainPoints = [
  "Raw vehicle telemetry is accurate but difficult to interpret as coaching feedback.",
  "Risk events need route context, not only timestamps and signal peaks.",
  "AI advice must explain deterministic evidence instead of repeating generic driving tips.",
];

const journeySteps = [
  "Trip auto-captured or demo generated",
  "Vehicle behaviour analysed",
  "Route-aware risk events detected",
  "AI coach explains evidence",
  "Next-drive target and history updated",
];

const architectureItems = [
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
];

const agentItems = [
  "LoadTripNode collects trip, route, metrics, events, and optional memory context.",
  "AnalyseEvidenceNode identifies the main behavioural pattern and top evidence.",
  "RetrieveKnowledgeNode selects RAG-lite snippets by event type, route context, and user question.",
  "GenerateCoachReportNode creates the coaching summary using DeepSeek when configured, or deterministic fallback.",
  "ValidateReportNode checks route relevance, evidence use, specificity, measurability, and overclaim control.",
  "ReviseReportNode repairs missing context or unsafe language before returning the structured report.",
];

const evaluationItems = [
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
];

const roadmapItems = [
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
];

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

function ConnectorDiagram() {
  return (
    <div className="grid gap-3 rounded-[28px] border border-forest-100 bg-white p-4 shadow-card md:grid-cols-5">
      {["Frontend", "Backend", "Analytics", "Agent", "Memory"].map((item, index) => (
        <div key={item} className="relative rounded-3xl border border-slate-200 bg-forest-50/50 p-4">
          <span className="text-xs font-bold uppercase tracking-[0.16em] text-forest-700">
            {String(index + 1).padStart(2, "0")}
          </span>
          <p className="mt-3 text-sm font-bold text-ink">{item}</p>
          {index < 4 ? (
            <span className="absolute -right-3 top-1/2 hidden h-px w-6 bg-forest-600 md:block" />
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function DocumentationSections() {
  return (
    <div className="mx-auto max-w-6xl space-y-8 px-6 pb-24">
      <section id="product" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader
          eyebrow="Product"
          title="A post-drive coaching product, not a raw telemetry dashboard."
          body="DriveCoach AI translates vehicle behaviour, route context, and optional wearable signals into a clear review: what happened, why it matters, and what to focus on next."
        />

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[28px] border border-slate-200 bg-white p-5">
            <h3 className="text-lg font-semibold text-ink">Core user pain points</h3>
            <div className="mt-5 space-y-3">
              {productPainPoints.map((point) => (
                <div key={point} className="flex gap-3 rounded-2xl bg-slate-50 p-3">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-forest-700" />
                  <p className="text-sm leading-6 text-slate-600">{point}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-forest-100 bg-forest-50 p-5">
            <h3 className="text-lg font-semibold text-ink">User journey</h3>
            <div className="mt-5 space-y-3">
              {journeySteps.map((step, index) => (
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
        <SectionHeader
          eyebrow="Architecture"
          title="A thin product UI on top of deterministic analysis and an observable agent layer."
          body="The frontend stays focused on the product story. The backend owns session generation, analysis, memory, agent workflow, and evaluation so future real telemetry can reuse the same contract."
        />

        <div className="mt-8">
          <ConnectorDiagram />
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {architectureItems.map((item) => (
            <article key={item.title} className="rounded-[26px] border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-ink">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="agent" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader
          eyebrow="Agent"
          title="The AI coach is a workflow, not a single prompt."
          body="The agent uses deterministic trip evidence, route context, RAG-lite knowledge, optional memory, and validation gates before returning a structured coaching report."
        />

        <div className="mt-8 grid gap-3">
          {agentItems.map((item, index) => (
            <div key={item} className="grid gap-3 rounded-3xl border border-slate-200 bg-white p-4 md:grid-cols-[120px_1fr] md:items-center">
              <span className="text-xs font-bold uppercase tracking-[0.18em] text-forest-700">
                Node {index + 1}
              </span>
              <p className="text-sm leading-6 text-slate-600">{item}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="evaluation" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader
          eyebrow="Evaluation"
          title="Trust comes from separating evidence, interpretation, and quality checks."
          body="Driving metrics are calculated before the AI speaks. The report is then evaluated for usefulness, route relevance, measurable guidance, and claim boundaries."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {evaluationItems.map((item) => (
            <article key={item.title} className="rounded-[28px] border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-ink">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.body}</p>
            </article>
          ))}
        </div>

        <div className="mt-5 rounded-[28px] border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-amber-800">Boundary</p>
          <p className="mt-2 text-sm leading-6 text-amber-900">
            Current thresholds are transparent coaching heuristics for the demo route. They are not universal safety limits and should be calibrated with labelled real or simulator data before operational use.
          </p>
        </div>
      </section>

      <section id="roadmap" className="scroll-mt-28 rounded-[36px] border border-forest-100 bg-white/90 p-6 shadow-card md:p-8">
        <SectionHeader
          eyebrow="Roadmap"
          title="Build the product story first, then add more data and stronger retrieval."
          body="The next phases prioritise presentation quality, bilingual access, real-data calibration, and production-grade knowledge retrieval without overcomplicating the current MVP."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {roadmapItems.map((item) => (
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
