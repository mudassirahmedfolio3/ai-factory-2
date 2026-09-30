import { useCallback, useEffect, useState } from "react";
import { fetchRandomBrief } from "../api";

export type ComplexityLevel = "basic" | "basic_plus" | "standard" | "full";

export const COMPLEXITY_OPTIONS: {
  id: ComplexityLevel;
  label: string;
  description: string;
  estimatedMinutes: number;
  maxReleases: number;
}[] = [
  {
    id: "basic",
    label: "Basic",
    description: "Mini PRD + build sketch, then open a mobile-style preview in your browser.",
    estimatedMinutes: 10,
    maxReleases: 1,
  },
  {
    id: "basic_plus",
    label: "Basic+",
    description:
      "Full discovery crew + client review, design, sprint, build, QA, and PRD-driven browser preview.",
    estimatedMinutes: 25,
    maxReleases: 1,
  },
  {
    id: "standard",
    label: "Standard",
    description: "Full SDLC with all crews and one release.",
    estimatedMinutes: 60,
    maxReleases: 1,
  },
  {
    id: "full",
    label: "Full",
    description: "Complete pipeline with multiple releases and change loops.",
    estimatedMinutes: 120,
    maxReleases: 2,
  },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    project_name: string;
    client_brief: string;
    complexity: ComplexityLevel;
    max_releases?: number;
  }) => void;
  loading: boolean;
}

export default function NewRunModal({ open, onClose, onSubmit, loading }: Props) {
  const [projectName, setProjectName] = useState("ecommerce-flutter-app");
  const [brief, setBrief] = useState("");
  const [briefSource, setBriefSource] = useState("");
  const [briefLoading, setBriefLoading] = useState(false);
  const [complexity, setComplexity] = useState<ComplexityLevel>("basic");
  const [maxReleases, setMaxReleases] = useState(2);
  const selected = COMPLEXITY_OPTIONS.find((o) => o.id === complexity)!;

  const loadRandomBrief = useCallback(async () => {
    setBriefLoading(true);
    try {
      const data = await fetchRandomBrief();
      setProjectName(data.project_name);
      setBrief(data.client_brief);
      setBriefSource(`${data.niche} · via ${data.source}`);
    } catch {
      setBriefSource("Could not reach web — using a local niche");
      setBrief(
        "Build a Flutter e-commerce MVP for a specialty tea shop with catalog, cart, checkout, and accounts.",
      );
      setProjectName("specialty-tea-shop");
    } finally {
      setBriefLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open && complexity === "basic" && !brief && !briefLoading) {
      void loadRandomBrief();
    }
  }, [open, complexity, brief, briefLoading, loadRandomBrief]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-white">Start New Factory Run</h2>
        <p className="mt-1 text-sm text-slate-400">
          Choose complexity — estimated time depends on Cursor CLI speed.
        </p>
        <form
          className="mt-4 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit({
              project_name: projectName,
              client_brief: brief,
              complexity,
              max_releases: complexity === "full" ? maxReleases : undefined,
            });
          }}
        >
          <fieldset className="space-y-2">
            <legend className="text-sm text-slate-400">Complexity</legend>
            {COMPLEXITY_OPTIONS.map((option) => (
              <label
                key={option.id}
                className={`flex cursor-pointer gap-3 rounded-lg border p-3 transition-colors ${
                  complexity === option.id
                    ? "border-cyan-500 bg-cyan-950/40"
                    : "border-slate-700 bg-slate-950 hover:border-slate-600"
                }`}
              >
                <input
                  type="radio"
                  name="complexity"
                  value={option.id}
                  checked={complexity === option.id}
                  onChange={() => setComplexity(option.id)}
                  className="mt-1"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-white">{option.label}</span>
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-cyan-300">
                      ~{option.estimatedMinutes} min
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{option.description}</p>
                </div>
              </label>
            ))}
          </fieldset>

          <p className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300">
            Selected: <strong className="text-white">{selected.label}</strong> — estimated{" "}
            <strong className="text-cyan-300">~{selected.estimatedMinutes} minutes</strong>
            {complexity === "basic" && " (2 AI steps + auto-pass gates)"}
          </p>

          <label className="block text-sm">
            <span className="text-slate-400">Project name</span>
            <input
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm">
            <span className="flex items-center justify-between text-slate-400">
              <span>Client brief</span>
              {complexity === "basic" && (
                <button
                  type="button"
                  disabled={briefLoading}
                  onClick={() => void loadRandomBrief()}
                  className="text-xs text-cyan-400 hover:text-cyan-300 disabled:opacity-50"
                >
                  {briefLoading ? "Fetching…" : "New random niche"}
                </button>
              )}
            </span>
            {complexity === "basic" && briefSource && (
              <p className="mt-1 text-xs text-slate-500">{briefSource}</p>
            )}
            {complexity === "basic" && (
              <p className="mt-1 text-xs text-slate-500">
                Basic runs always pull a fresh e-commerce niche from the web at kickoff.
              </p>
            )}
            <textarea
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              rows={4}
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder={
                complexity === "basic"
                  ? "Loading random e-commerce idea from the web…"
                  : "Describe the product you want built…"
              }
            />
          </label>
          {complexity === "full" && (
            <label className="block text-sm">
              <span className="text-slate-400">Max releases</span>
              <input
                type="number"
                min={2}
                max={5}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                value={maxReleases}
                onChange={(e) => setMaxReleases(Number(e.target.value))}
              />
            </label>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-4 py-2 text-sm text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
            >
              {loading ? "Starting…" : `Start ${selected.label} Run`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
