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

Apply ranking -> default model + fallback chain (run with the Hermes venv python, needs ruamel.yaml):

```
python apply_model_policy.py --dry-run
python apply_model_policy.py
hermes fallback list
```

See `SKILL.md` for the full ranking, Muse token discipline, the data-training note on `*-contributor`, and cron wiring.

## Remotes

- GitHub: `https://github.com/hguyswow/free-model-policy.git`
- NAS (personal): `ssh://aibackup@hguyswow.asuscomm.com:28/volume5/dev/git/free-model-policy.git`
