import type { PipelineStep } from "../types";

const statusStyles: Record<string, string> = {
  pending: "border-slate-700 bg-slate-900 text-slate-500",
  active: "border-cyan-400 bg-cyan-950/50 text-cyan-300 ring-2 ring-cyan-500/40",
  completed: "border-emerald-600 bg-emerald-950/40 text-emerald-300",
  failed: "border-red-500 bg-red-950/40 text-red-300",
};

const dotStyles: Record<string, string> = {
  pending: "bg-slate-600",
  active: "bg-cyan-400 animate-pulse",
  completed: "bg-emerald-400",
  failed: "bg-red-400",
};

interface Props {
  steps: PipelineStep[];
  phase: string;
}

export default function PipelineBoard({ steps, phase }: Props) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          SDLC Pipeline
        </h2>
        <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
          phase: {phase}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {steps.map((step) => (
          <div
            key={step.id}
            className={`flex min-w-[7rem] flex-1 items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium ${statusStyles[step.status] ?? statusStyles.pending}`}
          >
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${dotStyles[step.status] ?? dotStyles.pending}`}
            />
            {step.label}
          </div>
        ))}
      </div>
    </div>
  );
}
