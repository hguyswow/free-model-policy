#!/usr/bin/env python3
"""Create or update the daily free-model ranking cron so it re-applies the policy.

Usage: python wire_cron.py <absolute path to apply_model_policy.py>
Idempotent: creates the job if missing, otherwise rewrites only the apply step / script path.
"""
import json, os, re, subprocess, sys

NAME = "모델 목록 갱신 (무료모델)"
SCHEDULE = "0 9 * * *"
JOBS = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "cron", "jobs.json")


def prompt_for(apply_path):
    apply_path = apply_path.replace("\\", "/")
    return (
        "고성능 무료 모델 리스트 갱신 후 Hermes 설정에 반영. 순서: "
        "(1) Hermes agent venv python 을 자동 탐색(%LOCALAPPDATA%/hermes/installs/*/environments/*/venv/Scripts/python.exe 중 최신) 후 실행: "
        "from agent.models_dev import fetch_models_dev; d=fetch_models_dev(force_refresh=True); print(len(d)). "
        "(2) 같은 python 으로 %LOCALAPPDATA%/hermes/models_dev_cache.json 을 읽어 (a) openrouter 에서 :free 로 끝나는 모델 전수 "
        "(id, name, last_updated, cost, limit.context, reasoning, tool_call), (b) opencode-go/opencode 에서 cost.input==0 and cost.output==0 인 모델 전수 "
        "+ muse-spark-1.3-contributor(Go 포함) 별도 표기. "
        "(3) 성능 우선 순위(최신순 아님): OpenRouter 1 poolside/laguna-s-2.1:free, 2 thinkingmachines/inkling:free, 3 thinkingmachines/inkling-small:free, "
        "4 nvidia/nemotron-3-ultra-550b-a55b:free, 5 google/gemma-4-31b-it:free, 6 cohere/north-mini-code:free(코딩), 나머지는 last_updated 내림차순. "
        "OpenCode 1 longcat-2.5-preview-free, 2 space-bunny-free, 3 step-5-preview-free. 목록에서 사라진 모델은 제외. "
        "(4) %LOCALAPPDATA%/hermes/cache/free_models_ranked.json (ranked_openrouter/free_opencode/go_included/updated_at) 과 같은 경로 .md(사람용 표) 저장. "
        f"(5) 같은 python 으로 {apply_path} 를 실행해 랭킹을 Hermes 기본모델·fallback_providers 체인에 실제 반영(백업 자동). "
        "실패하면 config 를 건드리지 말고 오류만 보고. "
        "(6) FINAL RESPONSE 는 갱신시각 + OpenRouter 상위 5 + OpenCode 상위 3 + apply_model_policy.py 출력(적용된 기본모델/fallback 체인)만 간결히. "
        "질문 금지, 자율 완료."
    )


def find_job():
    if not os.path.exists(JOBS):
        return None
    data = json.load(open(JOBS, encoding="utf-8"))
    jobs = data if isinstance(data, list) else data.get("jobs", data)
    for job in (jobs.values() if isinstance(jobs, dict) else jobs):
        if isinstance(job, dict) and job.get("name") == NAME:
            return job
    return None


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    apply_path = os.path.abspath(sys.argv[1])
    job = find_job()
    if job is None:
        cmd = ["hermes", "cron", "create", "--name", NAME, "--deliver", "local", SCHEDULE, prompt_for(apply_path)]
        action = "created"
    else:
        old = job.get("prompt", "")
        if apply_path.replace("\\", "/") in old:
            print(f"cron '{NAME}' already applies {apply_path}")
            return 0
        jid = job.get("id") or job.get("job_id")
        cmd = ["hermes", "cron", "edit", jid, "--prompt", prompt_for(apply_path)]
        action = "updated"
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"hermes cron failed: {(r.stdout + r.stderr)[-400:]}")
    print(f"cron '{NAME}' {action} -> applies {apply_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
