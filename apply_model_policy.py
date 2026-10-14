#!/usr/bin/env python3
"""Apply the free-model ranking to Hermes config: default model + fallback_providers chain.

Run with the Hermes venv python (needs ruamel.yaml):
    python apply_model_policy.py [--config PATH] [--ranked PATH] [--dry-run]

Policy (see SKILL.md):
- Default = OpenRouter #1 strict-free model (absorbs most traffic).
- Fallback chain alternates providers so one rate limit never stalls the agent:
  OpenRouter #2 -> [Go muse-spark, only if data-training tiers are allowed] -> OpenCode strict-free #1
  -> OpenRouter #3 -> OpenRouter coding model.
- muse-spark sits in the chain, not as default, so its 5h/weekly token budget is spent only when
  OpenRouter is throttled (spreads usage, avoids Go limit hits).
"""
import argparse, datetime, json, os, shutil, sys
from ruamel.yaml import YAML

HERMES = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes")
MUSE = "muse-spark-1.3-contributor"
CODING = "cohere/north-mini-code:free"
MAX_CHAIN = 5
DEFAULT_RANKED = {  # mirrors "Current ranking" in SKILL.md
    "updated_at": "built-in",
    "ranked_openrouter": [{"id": i} for i in (
        "poolside/laguna-s-2.1:free", "thinkingmachines/inkling:free", "thinkingmachines/inkling-small:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free", CODING)],
    "free_opencode": [{"id": i} for i in ("longcat-2.5-preview-free", "space-bunny-free", "step-5-preview-free")],
}


def build(ranked, allow_training):
    orr = [m["id"] for m in ranked.get("ranked_openrouter", []) if m.get("tool_call", True)]
    oc = [m["id"] for m in ranked.get("free_opencode", []) if m.get("tool_call", True)]
    if not orr:
        raise SystemExit("ranked_openrouter is empty - run the ranking job first")
    default = ("openrouter", orr[0])
    chain = []
    if len(orr) > 1:
        chain.append(("openrouter", orr[1]))
    if allow_training:
        chain.append(("opencode-go", MUSE))
    if oc:
        chain.append(("opencode-go", oc[0]))
    if len(orr) > 2:
        chain.append(("openrouter", orr[2]))
    if CODING in orr:
        chain.append(("openrouter", CODING))
    seen, out = {default}, []
    for c in chain:
        if c not in seen:
            seen.add(c); out.append(c)
    return default, out[:MAX_CHAIN]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERMES, "config.yaml"))
    ap.add_argument("--ranked", default=os.path.join(HERMES, "cache", "free_models_ranked.json"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    yaml = YAML()
    yaml.preserve_quotes = True
    with open(a.config, encoding="utf-8") as f:
        cfg = yaml.load(f) or {}
    if os.path.exists(a.ranked):
        with open(a.ranked, encoding="utf-8") as f:
            ranked = json.load(f)
    else:  # fresh machine: the daily cron has not written a ranking yet
        print(f"note: {a.ranked} missing - using built-in ranking from SKILL.md")
        ranked = DEFAULT_RANKED

    allow = bool((cfg.get("security") or {}).get("allow_data_training_tiers_noninteractive", False))
    (dp, dm), chain = build(ranked, allow)

    print(f"ranking updated_at: {ranked.get('updated_at')}")
    print(f"default : {dp} / {dm}")
    for i, (p, m) in enumerate(chain, 1):
        print(f"fallback{i}: {p} / {m}")
    if not allow:
        print(f"note: {MUSE} skipped (data-training tier; set security.allow_data_training_tiers_noninteractive: true to include)")
    if a.dry_run:
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(a.config, f"{a.config}.bak_policy_{stamp}")
    cfg.setdefault("model", {})
    cfg["model"]["default"] = dm
    cfg["model"]["provider"] = dp
    cfg["fallback_providers"] = [{"provider": p, "model": m} for p, m in chain]
    tmp = a.config + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)
    os.replace(tmp, a.config)
    print(f"applied -> {a.config} (backup .bak_policy_{stamp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
