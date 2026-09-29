import type { AuditEvent } from "../types";

interface Props {
  events: AuditEvent[];
}

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}

const decisionColor = (decision: string) => {
  const d = decision.toLowerCase();
  if (d.includes("pass") || d === "approved" || d === "started") return "text-emerald-400";
  if (d.includes("fail") || d === "rejected" || d === "denied") return "text-red-400";
  if (d === "pending") return "text-amber-400";
  return "text-slate-300";
};

export default function ActivityFeed({ events }: Props) {
  const sorted = [...events].reverse();

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Activity Feed
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {sorted.length === 0 ? (
          <p className="text-sm text-slate-500">No events yet. Start a run to see activity.</p>
        ) : (
          <ul className="space-y-2">
            {sorted.map((ev, i) => (
              <li
                key={`${ev.timestamp}-${ev.event}-${i}`}
                className="rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-sm"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-slate-200">{ev.event.replace(/_/g, " ")}</span>
                  <span className="text-xs text-slate-500">{formatTime(ev.timestamp)}</span>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs">
                  <span className="text-slate-500">{ev.agent}</span>
                  <span className={`font-semibold ${decisionColor(ev.decision)}`}>
                    {ev.decision}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
