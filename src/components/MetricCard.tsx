type MetricCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: "default" | "green" | "amber";
};

const toneClass = {
  default: "border-slate-200 bg-white",
  green: "border-forest-100 bg-forest-50",
  amber: "border-amber-100 bg-amber-50",
};

export function MetricCard({ label, value, helper, tone = "default" }: MetricCardProps) {
  return (
    <div className={`rounded-2xl border p-4 shadow-sm ${toneClass[tone]}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-ink">{value}</p>
      {helper ? <p className="mt-1 text-xs leading-5 text-slate-500">{helper}</p> : null}
    </div>
  );
}
