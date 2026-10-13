# free-model-policy

Hermes multi-machine zero-cost model policy (OpenRouter + OpenCode Go).

- No API keys, tokens, or secrets in this repo (verified).
- Load `SKILL.md` on each machine, then apply:

```
hermes config set model.default "poolside/laguna-s-2.1:free"
hermes config set model.provider "openrouter"
```

Go workhorse alternative:

```
hermes config set model.default "muse-spark-1.3-contributor"
hermes config set model.provider "opencode-go"
```

See `SKILL.md` for the full ranking, Muse token discipline, and cron wiring.
