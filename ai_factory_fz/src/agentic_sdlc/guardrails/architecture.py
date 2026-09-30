"""Guardrails on the Architect's output. Each rule returns a list of problems (empty = passes).

Rules are code checks: free, instant, deterministic. The app-type facts they check against (allowed
stack, platform, API prefix, health path, money fields...) come from the profile's `guardrails:`
section and `release:` section; which rules are on comes from the pipeline's `guardrails.architect`.
A failing design goes back to the Architect with the list of problems (the task's retry loop).

  A1 stack conformance         B1 prose matches contract    C1 entities exist        D1 3+ complete ADRs
  A2 mobile platform           B2 health endpoint           C2 money as integers     D2 security basics
                               B3 API prefix                C3 id + timestamps       D3 no secrets
                               B4 shared error schema
                               B5 typed responses
                               B6 auth per operation
"""

import re
from typing import Any, Callable

import yaml

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.guardrails import secrets
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.release.contract import operations as contract_operations
from agentic_sdlc.release.contract import strip_prefix

ALL_RULES = ["A1", "A2", "B1", "B2", "B3", "B4", "B5", "B6", "C1", "C2", "C3", "D1", "D2", "D3"]
_METHODS = {"get", "post", "put", "patch", "delete"}
_PARAM = re.compile(r"\{[^}]+\}|:[A-Za-z_]\w*")


class Context:
    """What the rules check against: the design, its parsed contract, and the profile's facts."""

    def __init__(self, arch: ArchitectureDoc, profile: Profile):
        self.arch = arch
        self.profile = profile
        self.g: dict[str, Any] = profile.guardrails or {}
        self.prefix = profile.release.api_prefix
        try:
            self.spec = yaml.safe_load(arch.openapi_yaml) or {}
        except yaml.YAMLError:
            self.spec = {}
        if not isinstance(self.spec, dict):
            self.spec = {}

    def ops(self) -> list[tuple[str, str, dict]]:
        """(METHOD, path, operation) for every operation in the contract."""
        out = []
        for path, item in (self.spec.get("paths") or {}).items():
            for method, op in (item or {}).items():
                if method in _METHODS and isinstance(op, dict):
                    out.append((method.upper(), path, op))
        return out

    def resolve(self, node: Any) -> Any:
        """Follow a local $ref (#/components/...)."""
        while isinstance(node, dict) and isinstance(node.get("$ref"), str) and node["$ref"].startswith("#/"):
            target: Any = self.spec
            for part in node["$ref"][2:].split("/"):
                target = target.get(part, {}) if isinstance(target, dict) else {}
            node = target
        return node

    def text(self) -> str:
        a = self.arch
        parts = [a.overview, a.data_model_notes, *a.security, a.openapi_yaml, a.prisma_schema]
        parts += [f"{d.context} {d.decision} {d.consequences}" for d in a.adrs]
        parts += [f"{c.name} {c.responsibility} {c.technology}" for c in a.components]
        return "\n".join(parts)


def _norm(name: str) -> str:
    return re.sub(r"[\s_\-]", "", name).lower()


def _has_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])", text.lower()) is not None


def _prisma_models(schema: str) -> dict[str, list[tuple[str, str, str]]]:
    """model name -> [(field, type, rest of line)]."""
    models: dict[str, list[tuple[str, str, str]]] = {}
    for m in re.finditer(r"^model\s+(\w+)\s*\{(.*?)^\}", schema, flags=re.M | re.S):
        fields = []
        for line in m.group(2).splitlines():
            line = line.split("//")[0].strip()
            parts = line.split(None, 2)
            if len(parts) >= 2 and not line.startswith("@@"):
                fields.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
        models[m.group(1)] = fields
    return models


# ---------- A. stack and platform ----------

def a1_stack(c: Context) -> list[str]:
    """No technology outside the profile's stack, and the profile's core stack is used."""
    forbidden = [t.lower() for t in c.g.get("forbidden_stack", [])]
    required = c.g.get("required_stack", [])
    errors = []
    for comp in c.arch.components:
        bad = [t for t in forbidden if _has_term(comp.technology, t)]
        if bad:
            errors.append(f"A1: component '{comp.name}' uses {', '.join(bad)}, which is outside this profile's stack")
    techs = " ".join(comp.technology for comp in c.arch.components)
    errors += [f"A1: the design does not use {t}, which is part of this profile's stack" for t in required
               if not _has_term(techs, t)]
    return errors


def a2_platform(c: Context) -> list[str]:
    platform = c.g.get("platform")
    if not platform:
        return []
    errors = []
    if not c.arch.app_features:
        errors.append(f"A2: the design has no app features; this profile builds a {platform} app")
    required = c.g.get("platform_technology", "")
    if required and not any(_has_term(comp.technology, required) for comp in c.arch.components):
        errors.append(f"A2: no component uses {required}; the app must be a {platform} app")
    text = " ".join([c.arch.overview, *(f"{f.name} {' '.join(f.screens)} {f.state_management}" for f in c.arch.app_features),
                     *(f"{comp.name} {comp.technology}" for comp in c.arch.components)])
    for term in c.g.get("forbidden_platforms", []):
        if _has_term(text, term):
            errors.append(f"A2: the design targets '{term}'; this profile builds {platform} apps only")
    return errors


# ---------- B. API contract ----------

def b1_prose_matches_contract(c: Context) -> list[str]:
    listed = set()
    for m in c.arch.backend_modules:
        for e in m.endpoints:
            parts = e.strip().split()
            if len(parts) >= 2 and parts[0].lower() in _METHODS:
                path = strip_prefix(parts[1].split("?")[0], c.prefix)
                listed.add(f"{parts[0].upper()} {_PARAM.sub('{}', path.rstrip('/') or '/')}")
    contract = contract_operations(c.spec, c.prefix)
    errors = [f"B1: module endpoint {e} is not in openapi.yaml" for e in sorted(listed - contract)]
    errors += [f"B1: openapi.yaml operation {e} is not listed under any backend module" for e in sorted(contract - listed)]
    return errors


def b2_health(c: Context) -> list[str]:
    health = c.profile.release.health_path
    if not health:
        return []
    want = f"GET {_PARAM.sub('{}', strip_prefix(health, c.prefix))}"
    return [] if want in contract_operations(c.spec, c.prefix) else [f"B2: the contract has no {want} (health check)"]


def b3_prefix(c: Context) -> list[str]:
    if not c.prefix:
        return []
    servers = c.spec.get("servers") or []
    urls = [s.get("url", "") for s in servers if isinstance(s, dict)]
    if not urls:
        return [f"B3: the contract has no servers entry; the API base must end with {c.prefix}"]
    bad = [u for u in urls if not u.rstrip("/").endswith(c.prefix)]
    return [f"B3: server URL '{u}' does not end with the API prefix {c.prefix}" for u in bad]


def b4_error_schema(c: Context) -> list[str]:
    infra = {_PARAM.sub("{}", strip_prefix(p, c.prefix)) for p in
             (c.profile.release.health_path, c.profile.release.openapi_json_path) if p}
    errors, refs = [], set()
    for method, path, op in c.ops():
        if _PARAM.sub("{}", strip_prefix(path, c.prefix)) in infra:
            continue  # health / API docs have no client errors
        responses = op.get("responses") or {}
        codes = [code for code in responses if str(code)[:1] in ("4", "5") or str(code) == "default"]
        if not codes:
            errors.append(f"B4: {method} {path} declares no error response (4xx/5xx)")
            continue
        for code in codes:
            resp = c.resolve(responses[code])
            schema = ((resp.get("content") or {}).get("application/json") or {}).get("schema") if isinstance(resp, dict) else None
            ref = schema.get("$ref") if isinstance(schema, dict) else None
            if not ref:
                errors.append(f"B4: {method} {path} {code} does not use a shared error schema ($ref)")
            else:
                refs.add(ref)
    if len(refs) > 1:
        errors.append(f"B4: error responses use {len(refs)} different schemas ({', '.join(sorted(refs))}); use one shared schema")
    return errors


def b5_typed_responses(c: Context) -> list[str]:
    errors = []
    for method, path, op in c.ops():
        for code, resp in (op.get("responses") or {}).items():
            if str(code).startswith("2") and str(code) != "204":
                resp = c.resolve(resp)
                content = resp.get("content") if isinstance(resp, dict) else None
                if not content or not any(isinstance(v, dict) and v.get("schema") for v in content.values()):
                    errors.append(f"B5: {method} {path} {code} response has no schema")
    return errors


def b6_auth_per_operation(c: Context) -> list[str]:
    if "security" in c.spec:
        return []  # a global default is an explicit decision; operations may override it
    return [f"B6: {method} {path} does not say whether it is secured (add security, or security: [] if public)"
            for method, path, op in c.ops() if "security" not in op]


# ---------- C. data model ----------

def c1_entities_exist(c: Context) -> list[str]:
    models = {_norm(m) for m in _prisma_models(c.arch.prisma_schema)}
    errors = []
    for m in c.arch.backend_modules:
        for e in m.entities:
            name = re.split(r"\s*[(\[]|\s+via\s+", e.strip())[0]   # "User (password fields)" -> "User"
            if name and name != "-" and _norm(name) not in models:
                errors.append(f"C1: module '{m.name}' uses entity '{e}', which is not a model in schema.prisma")
    return errors


def c2_money_integers(c: Context) -> list[str]:
    words = [w.lower() for w in c.g.get("money_fields", ["price", "amount", "total", "subtotal", "cost"])]
    errors = []
    for model, fields in _prisma_models(c.arch.prisma_schema).items():
        for name, ftype, _ in fields:
            base = ftype.rstrip("?[]")
            if base in ("Float", "Decimal") and any(w in name.lower() for w in words):
                errors.append(f"C2: {model}.{name} is {base}; store money as Int (minor units, e.g. cents)")
    return errors


def c3_ids_and_timestamps(c: Context) -> list[str]:
    errors = []
    for model, fields in _prisma_models(c.arch.prisma_schema).items():
        names = {n for n, _, _ in fields}
        has_id = any("@id" in rest for _, _, rest in fields) or re.search(
            rf"^model\s+{model}\s*\{{.*?@@id", c.arch.prisma_schema, flags=re.M | re.S) is not None
        if not has_id:
            errors.append(f"C3: model {model} has no @id")
        missing = [t for t in ("createdAt", "updatedAt") if t not in names]
        if missing:
            errors.append(f"C3: model {model} is missing {', '.join(missing)}")
    return errors


# ---------- D. decisions and security ----------

def d1_adrs(c: Context) -> list[str]:
    minimum = c.g.get("min_adrs", 3)
    errors = [f"D1: {len(c.arch.adrs)} ADRs; at least {minimum} are needed for the key decisions"] \
        if len(c.arch.adrs) < minimum else []
    for a in c.arch.adrs:
        empty = [f for f in ("context", "decision", "consequences") if len(getattr(a, f).strip()) < 20]
        if empty:
            errors.append(f"D1: {a.id} has an empty or one-word {', '.join(empty)}")
    return errors


def d2_security_basics(c: Context) -> list[str]:
    topics: dict[str, list[str]] = c.g.get("security_topics", {
        "authentication": ["auth", "jwt", "token", "session", "credential"],
        "input validation": ["validat", "sanitiz"],
        "secrets and configuration": ["secret", "environment variable", "env var", "config"],
    })
    text = " ".join(c.arch.security).lower()
    return [f"D2: the security design does not address {topic}" for topic, words in topics.items()
            if not any(w in text for w in words)]


def d3_no_secrets(c: Context) -> list[str]:
    return [f"D3: the design contains what looks like {what}; use a placeholder or an environment variable"
            for what in secrets.find(c.text())]


RULES: dict[str, Callable[[Context], list[str]]] = {
    "A1": a1_stack, "A2": a2_platform,
    "B1": b1_prose_matches_contract, "B2": b2_health, "B3": b3_prefix, "B4": b4_error_schema,
    "B5": b5_typed_responses, "B6": b6_auth_per_operation,
    "C1": c1_entities_exist, "C2": c2_money_integers, "C3": c3_ids_and_timestamps,
    "D1": d1_adrs, "D2": d2_security_basics, "D3": d3_no_secrets,
}


def enabled_rules(pipeline: dict[str, Any]) -> list[str]:
    """Rules switched on in the pipeline (`guardrails.architect`: a list, or 'all'). Default: all."""
    setting = (pipeline.get("guardrails") or {}).get("architect", "all")
    if setting == "all":
        return list(ALL_RULES)
    unknown = [r for r in setting if r not in RULES]
    if unknown:
        raise ValueError(f"Unknown architect guardrails in pipeline config: {unknown} (known: {ALL_RULES})")
    return list(setting)


def check(arch: ArchitectureDoc, profile: Profile, rules: list[str]) -> list[str]:
    ctx = Context(arch, profile)
    return [problem for rule in rules for problem in RULES[rule](ctx)]


def checker(profile: Profile, pipeline: dict[str, Any]) -> Callable[[ArchitectureDoc], list[str]]:
    rules = enabled_rules(pipeline)
    return lambda arch: check(arch, profile, rules)
