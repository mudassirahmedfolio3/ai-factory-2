"""Compare the running API's OpenAPI document with the approved contract (docs/openapi.yaml)."""

import json
import re
from urllib.parse import urlparse

import yaml

_METHODS = {"get", "post", "put", "patch", "delete"}
_PARAM = re.compile(r"\{[^}]+\}|:[A-Za-z_]\w*")


def _base_path(spec: dict) -> str:
    servers = spec.get("servers") or []
    return urlparse(servers[0].get("url", "")).path.rstrip("/") if servers else ""


def operations(spec: dict, prefix: str = "") -> set[str]:
    """'METHOD /path' relative to the API prefix, with parameter names erased.

    The contract usually puts /api/v1 in `servers` while a framework-generated document
    puts it in each path; joining the base path and stripping the prefix makes both comparable.
    """
    base = _base_path(spec)
    ops = set()
    for path, item in (spec.get("paths") or {}).items():
        # Some generators put the prefix in both `servers` and each path: don't apply it twice.
        full = path if (prefix and path.startswith(prefix + "/")) or path == prefix else base + path
        if prefix and full.startswith(prefix):
            full = full[len(prefix):]
        norm = _PARAM.sub("{}", full.rstrip("/") or "/")
        for method in item or {}:
            if method.lower() in _METHODS:
                ops.add(f"{method.upper()} {norm}")
    return ops


def strip_prefix(path: str, prefix: str) -> str:
    return path[len(prefix):] if prefix and path.startswith(prefix) else path


def contract_diff(contract_yaml: str, served_json: str, api_prefix: str, ignore_paths: list[str] | None = None) -> list[str]:
    """Human-readable differences; empty when the API serves exactly the contract's operations.
    `ignore_paths` (full paths, e.g. the health check and the OpenAPI document) are infrastructure
    endpoints: they may or may not be in the contract."""
    contract = yaml.safe_load(contract_yaml)
    try:
        served = json.loads(served_json)
    except json.JSONDecodeError:
        return ["The API does not serve a valid OpenAPI JSON document"]
    ignored = {_PARAM.sub("{}", strip_prefix(p, api_prefix).rstrip("/") or "/") for p in (ignore_paths or []) if p}
    keep = lambda ops: {op for op in ops if op.split(" ", 1)[1] not in ignored}
    want, have = keep(operations(contract, api_prefix)), keep(operations(served, api_prefix))
    issues = [f"Missing in the API: {op}" for op in sorted(want - have)]
    issues += [f"Not in the contract: {op}" for op in sorted(have - want)]
    return issues
