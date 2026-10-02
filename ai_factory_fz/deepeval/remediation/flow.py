"""RemediationFlow, stage 1: report -> Project Manager triage and backlog -> human approval.

Steps 3-6 (fix loop, integration, QA and smoke, re-evaluation) are added in later stages."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from remediation.context import gather_context
from remediation.findings import ReportFormatError, extract_findings, load_report
from remediation.planner import plan_backlog
from remediation.schemas import Finding, RemediationBacklog, TriageResult
from remediation.status import RemediationStatus, refresh_report_headers
from remediation.triage import triage_findings
from remediation.validation import check_backlog, check_triage


APPROVAL_STATUSES = ("proposed", "approved", "rejected")


class RemediationError(RuntimeError):
    pass


class RemediationFlow:
    def __init__(self, run_dir: Path, runner, report_path: Path | None = None):
        self.run_dir = Path(run_dir).resolve()
        self.runner = runner
        self.report_path = Path(report_path) if report_path else None
        self.dir = self.run_dir / "remediation"
        self.status = RemediationStatus.load(self.dir / "status.json")

    # ---------- helpers ----------

    def _save(self) -> None:
        self.status.save(self.dir / "status.json")
        refresh_report_headers(self.run_dir, self.status)

    def _set(self, key: str, state: str, reason: str = "") -> None:
        self.status.set(key, state, reason)  # type: ignore[arg-type]
        self._log("step", step=key, state=state, reason=reason)   # the record first: a failing save cannot lose it
        self._save()

    def _log(self, event: str, **data) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with (self.dir / "history.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "event": event, **data}) + "\n")

    def _write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)

    def _copy_atomic(self, source: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp")
        shutil.copyfile(source, tmp)
        tmp.replace(dest)

    def _begin(self, key: str) -> None:
        """Enter 'running' unless a crashed earlier attempt already left the step there."""
        if self.status.step(key).state != "running":
            self._set(key, "running")

    def _write_json(self, name: str, model) -> None:
        self._write_text(self.dir / name, model.model_dump_json(indent=2))

    def _find_report(self) -> Path | None:
        if self.report_path:
            return self.report_path if self.report_path.is_file() else None
        candidates = sorted(self.run_dir.glob("eval_report*.json"), key=lambda p: p.stat().st_mtime)
        return candidates[-1] if candidates else None

    # ---------- step 1 ----------

    def _step_report(self) -> bool:
        baseline = self.dir / "baseline" / "eval_report.json"
        if self.status.step("report").state == "done":
            if baseline.is_file():
                self._note_newer_report(baseline)
                return True
            raise RemediationError(
                f"The baseline report is missing ({baseline}). "
                "Restore it from a backup, or delete remediation/status.json to start the cycle again.")
        self.dir.mkdir(parents=True, exist_ok=True)
        self._save()
        self._begin("report")   # also valid from blocked/failed: a new attempt after the report was supplied or fixed
        source = self._find_report()
        if source is None:
            self._set("report", "blocked", f"DeepEval report not found: {self.report_path or self.run_dir / 'eval_report*.json'}")
            return False
        if not baseline.is_file():
            try:
                extract_findings(load_report(source))   # validate before it becomes the baseline
            except ReportFormatError as e:
                self._set("report", "failed", str(e))
                return False
            self._copy_atomic(source, baseline)
        self._set("report", "done", f"baseline saved from {source.name}")
        return True

    def _note_newer_report(self, baseline: Path) -> None:
        source = self._find_report()
        try:
            differs = source is not None and source.read_bytes() != baseline.read_bytes()
        except OSError:
            return
        if differs:
            self._log("new_report_ignored", report=str(source))
            line = "A newer DeepEval report was supplied; the baseline from the first report is kept until the next round."
            if line not in self.status.note:
                self.status.note = f"{self.status.note}\n{line}".strip()
            self._save()

    # ---------- step 2 ----------

    def _step_triage(self) -> None:
        if self.status.step("triage").state in ("awaiting_approval", "done"):
            return
        self._begin("triage")
        try:
            findings = extract_findings(load_report(self.dir / "baseline" / "eval_report.json"))
            self._write_text(self.dir / "findings.json", json.dumps([f.model_dump() for f in findings], indent=2))
            if not findings:
                self._write_backlog(RemediationBacklog(summary="The report has no failed tests or gaps.", tasks=[]))
                self._set("triage", "done", "Nothing to remediate: the report has no failed tests or gaps")
                return
            context = gather_context(self.run_dir)
            triage = self._cached("triage.json", TriageResult, lambda t: check_triage(t, findings, self.run_dir))
            backlog = None
            if triage is None:
                triage = self._run_triage(findings, context)   # a new triage invalidates any cached backlog
            else:
                backlog = self._cached("backlog.json", RemediationBacklog, lambda b: check_backlog(b, findings, triage))
            if backlog is None:
                backlog = self._run_plan(findings, triage, context)
            backlog.limitations = sorted({*backlog.limitations, *(x[2:] for x in context["limitations"].splitlines() if x.startswith("- "))})
            self._write_backlog(backlog)
            self._set("triage", "awaiting_approval",
                      f"{len(backlog.tasks)} task(s) in remediation/backlog.md. Review it, then run: remediate approve")
        except ReportFormatError as e:
            self._set("triage", "failed", str(e))
        except Exception as e:
            try:
                self._set("triage", "failed", f"{type(e).__name__}: {e}")
            except Exception:
                pass   # keep the original error visible
            raise

    def _cached(self, name: str, model, check=None):
        """A saved artifact if it parses and passes the same guardrail as fresh model output, else None."""
        path = self.dir / name
        if not path.is_file():
            return None
        try:
            obj = model.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValidationError, ValueError, OSError) as e:
            self._log("cache_invalid", file=name, error=str(e)[:500])
            return None
        errors = check(obj) if check else []
        if errors:
            self._log("cache_invalid", file=name, error=errors[0][:500])
            return None
        return obj

    def _run_triage(self, findings: list[Finding], context: dict[str, str]) -> TriageResult:
        triage, usage = triage_findings(self.runner, findings, context, self.run_dir)
        self._write_json("triage.json", triage)
        self._log("triage", tokens=usage.total_tokens, model=usage.model)
        return triage

    def _run_plan(self, findings: list[Finding], triage: TriageResult, context: dict[str, str]) -> RemediationBacklog:
        backlog, usage = plan_backlog(self.runner, findings, triage, context)
        self._log("plan", tokens=usage.total_tokens, model=usage.model, tasks=len(backlog.tasks))
        return backlog

    def _write_backlog(self, backlog: RemediationBacklog) -> None:
        self._write_json("backlog.json", backlog)
        self._write_text(self.dir / "backlog.md", backlog.to_markdown())

    # ---------- public ----------

    def run(self) -> RemediationStatus:
        if self.dir.is_dir():
            refresh_report_headers(self.run_dir, self.status)   # DeepEval may have rewritten a report since the last run
        if self._step_report():
            self._step_triage()
        return self.status

    def approve(self) -> RemediationStatus:
        if self.status.step("triage").state != "awaiting_approval":
            raise RemediationError(
                f"The backlog is not waiting for approval (triage is {self.status.step('triage').state})")
        findings = self._load_required("findings.json", TypeAdapter(list[Finding]))
        triage = self._load_required("triage.json", TriageResult)
        backlog = self._load_required("backlog.json", RemediationBacklog)
        errors = self._approval_errors(backlog, findings, triage)
        if errors:
            raise RemediationError("The backlog is not valid, fix remediation/backlog.json first:\n- " + "\n- ".join(errors))
        for task in backlog.tasks:
            if task.status == "proposed":
                task.status = "approved"
        self._write_backlog(backlog)
        self._set("triage", "done", f"Approved {sum(t.status == 'approved' for t in backlog.tasks)} task(s)")
        self.status.note = "Backlog approved. The fix loop (steps 3-6) is not implemented yet; it starts here in stage 2."
        self._save()
        return self.status

    def _load_required(self, name: str, model):
        path = self.dir / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            raise RemediationError(f"remediation/{name} is missing; re-run the remediation to regenerate it") from None
        try:
            return (model.validate_json if isinstance(model, TypeAdapter) else model.model_validate_json)(text)
        except (ValidationError, ValueError) as e:
            raise RemediationError(f"remediation/{name} is not valid ({str(e).splitlines()[0]}); fix it or re-run the remediation") from None

    @staticmethod
    def _approval_errors(backlog: RemediationBacklog, findings: list[Finding], triage: TriageResult) -> list[str]:
        errors = [f"{t.id} has status '{t.status}'; only proposed, approved or rejected are allowed at approval"
                  for t in backlog.tasks if t.status not in APPROVAL_STATUSES]
        errors += check_backlog(backlog, findings, triage)   # a rejected task does not cover its findings
        return errors
