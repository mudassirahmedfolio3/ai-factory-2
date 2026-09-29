export type StepStatus = "pending" | "active" | "completed" | "failed";

export interface PipelineStep {
  id: string;
  label: string;
  status: StepStatus;
}

export interface RunState {
  run_id: string;
  project_name: string;
  phase: string;
  status: string;
  release_number: number;
  complexity?: string;
  estimated_minutes?: number;
  updated_at: string;
  pipeline_steps: PipelineStep[];
  checks: Record<string, boolean>;
  approvals: Record<string, string | null>;
  artifacts_index: { path: string; category: string }[];
  is_live?: boolean;
  error?: string;
}

export interface AuditEvent {
  timestamp: string;
  event: string;
  decision: string;
  agent: string;
  details?: Record<string, unknown>;
}
