---
name: free-model-policy
description: 'Use when choosing free AI models. Enforce zero-cost rule.'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [models, openrouter, opencode, cost]
    related_skills: [hermes-ops]
---

# Free Model Policy

Zero-cost model discipline for Hermes agents running on OpenRouter + OpenCode Go.

## When to Use

- Choosing or switching the Hermes main model under a free-only rule.
- Comparing OpenRouter `:free` models or OpenCode Go plan-included models by benchmark.
- Wiring or reviewing the daily free-model ranking cron job.
- Don't use for paid-model work or API-key setup; this skill never handles secrets.

## Rules

- Prefer highest-benchmark free model, never newest-by-date alone; latest `last_updated` is only a tiebreaker.
- Treat OpenRouter `:free`-suffixed IDs as the only strict-free set; anything with nonzero cost is paid even if cheap.
- Treat `muse-spark-1.3-contributor` on OpenCode Go as plan-included (no extra metered charge inside Go limits), not as strict $0; keep it separate from `-free` models.
- Switch with `hermes config set model.default "<id>"` plus `hermes config set model.provider "<provider>"`, then verify with `hermes config get model.default` and `hermes status`.
- Refresh the ranking daily from `models_dev_cache.json` via `fetch_models_dev(force_refresh=True)`; ETag makes it cheap when unchanged.
- Never store API keys, tokens, or `sk-*` values inside this skill, snapshots, or git repos.

## Current ranking (refresh daily, performance first)

- OpenRouter 1st `poolside/laguna-s-2.1:free` because Terminal-Bench 2.1 70.2% is best among free agent models.
- OpenRouter 2nd `thinkingmachines/inkling:free` because SWE-Verified 77.6% and GPQA 87.2% lead reasoning, but Terminal-Bench trails Laguna.
- OpenRouter 3rd `thinkingmachines/inkling-small:free` because it tracks Inkling at lower cost when 1M context is needed.
- OpenRouter 4th `nvidia/nemotron-3-ultra-550b-a55b:free` because SWE/GPQA are strong but Terminal-Bench 56.4% is weak for agent work.
- OpenRouter coding fallback `cohere/north-mini-code:free` for practical software edits.
- OpenCode strict-free 1st `longcat-2.5-preview-free` (Unlimited, limited-time), 2nd `space-bunny-free`, 3rd `step-5-preview-free`.
- OpenCode Go workhorse `muse-spark-1.3-contributor` because SWE ~77.4-class with generous limits (45,300 req/5h, $60 monthly meter).

## Muse token discipline (avoid 429/limit hits)

- Keep prompt cache alive: continue sessions instead of splitting, avoid parallel subagent bursts, and do not resend large files every turn.
- Keep outputs concise because output tokens cost ~100x cached input.
- Offload bulk/low-value work to Unlimited strict-free models (`longcat-2.5-preview-free`, `space-bunny-free`).
- On 429/limit, switch immediately to a strict-free model, then check remaining quota in the OpenCode console.
- Keep `Use balance` OFF so over-limit requests block instead of charging Zen credits.
- Remember Go accounting is monthly dollars with 5h=20% and weekly=50% sublimits; Muse averages ~620 fresh + ~71,400 cached + ~300 output tokens per request.

## Cron wiring

- Keep one daily job (`every day at 9am`) that force-refreshes the catalog and writes `cache/free_models_ranked.json` plus `cache/free_models_ranked.md` with ready-to-paste `hermes config set` commands.
- Auto-discover the agent venv python (`installs/*/environments/*/venv/Scripts/python.exe`, newest first); never hardcode a venv path because `hermes update` rotates it.
- Deliver `local` and keep the prompt self-contained because cron runs have no chat context.
