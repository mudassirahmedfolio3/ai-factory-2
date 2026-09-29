import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { fetchArtifact } from "../api";

interface Props {
  artifacts: { path: string; category: string }[];
  runId?: string;
  activePhase?: string;
}

const phaseArtifactHints: Record<string, string[]> = {
  discovery: ["requirements"],
  design: ["design"],
  code_review: ["review"],
  security: ["security"],
  qa: ["qa"],
  release: ["releases", "governance"],
  deployment: ["deploy"],
};

export default function ArtifactPanel({ artifacts, runId, activePhase }: Props) {
  const [selected, setSelected] = useState<string>("");
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (artifacts.length === 0) {
      setSelected("");
      setContent("");
      return;
    }

    const hints = activePhase ? phaseArtifactHints[activePhase] : undefined;
    const preferred = hints
      ? artifacts.find((a) => hints.some((h) => a.path.startsWith(h)))
      : undefined;
    const next = preferred?.path ?? artifacts[artifacts.length - 1]?.path ?? "";
    setSelected(next);
  }, [artifacts, activePhase]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    fetchArtifact(selected, runId)
      .then((res) => setContent(res.content))
      .catch(() => setContent("*Failed to load artifact.*"))
      .finally(() => setLoading(false));
  }, [selected, runId]);

  const categories = [...new Set(artifacts.map((a) => a.category))];

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Artifacts
        </h2>
        <div className="mt-2 flex flex-wrap gap-1">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => {
                const match = artifacts.find((a) => a.category === cat);
                if (match) setSelected(match.path);
              }}
              className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300 hover:bg-slate-700"
            >
              {cat}
            </button>
          ))}
        </div>
        {artifacts.length > 0 && (
          <select
            className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-300"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {artifacts.map((a) => (
              <option key={a.path} value={a.path}>
                {a.path}
              </option>
            ))}
          </select>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-4 prose prose-invert prose-sm max-w-none">
        {loading ? (
          <p className="text-slate-500">Loading…</p>
        ) : content ? (
          <ReactMarkdown>{content}</ReactMarkdown>
        ) : (
          <p className="text-slate-500">Select an artifact or start a run.</p>
        )}
      </div>
    </div>
  );
}
