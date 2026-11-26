#!/usr/bin/env python3
"""
Unicollect Full Model Warm-Up & Keep-Alive Script.

Warms up Mini (gpt-oss:20b), 1.2 (lfm2.5:24b-a2b-q4_0), and optionally ALL installed
Ollama models using the EXACT same /api/chat payload & KV-cache prefix as app/main.py.

Usage:
  python3 scripts/warm_all.py            # Warm configured Mini + 1.2 models once
  python3 scripts/warm_all.py --all      # Warm ALL installed Ollama models
  python3 scripts/warm_all.py --watch    # Warm now and keep models pinned forever
"""
import argparse
import os
import sys
import time
from pathlib import Path
from typing import List

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import (
    MATH_MODEL_LABEL,
    MAX_REPLY_TOKENS,
    MODEL_LABEL,
    OLLAMA_BASE_URL,
    OLLAMA_MATH_MODEL,
    OLLAMA_MODEL,
    SYSTEM_PROMPT,
    _get_loaded_ollama_models,
    _ensure_clean_engine_switch,
    _host_ram_gb,
)


def log(msg: str) -> None:
    print(f"[warm_all] {msg}", flush=True)


def wait_for_ollama(timeout_sec: int = 120) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            r = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=3)
            if r.ok:
                ver = r.json().get("version", "unknown")
                log(f"Ollama online (v{ver}) at {OLLAMA_BASE_URL}")
                return True
        except Exception:
            pass
        time.sleep(2.0)
    log(f"ERROR: Ollama did not respond at {OLLAMA_BASE_URL} within {timeout_sec}s")
    return False


def list_installed_models() -> List[str]:
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if r.ok:
            return [str(m.get("name", "")).strip() for m in r.json().get("models", []) if m.get("name")]
    except Exception as exc:
        log(f"Failed to list installed models: {exc}")
    return []


def warm_model(model_name: str, label: str) -> bool:
    t0 = time.time()
    # OOM-safe: strictly unload any other loaded model and wait for RAM release before loading on <28GB hosts
    _ensure_clean_engine_switch(model_name)
    is_lfm = model_name.lower().startswith("lfm")
    sys_prompt = SYSTEM_PROMPT.replace("{MODEL_NAME}", label)
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": "hi"},
        ],
        "stream": True,
        "keep_alive": -1,
        "options": {
            "temperature": 0.35 if is_lfm else 0.55,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.08,
            "num_predict": MAX_REPLY_TOKENS if MAX_REPLY_TOKENS > 0 else 4096,
        },
    }
    payload["think"] = "low" if model_name.lower().startswith("gpt-oss") else True
    log(f"Warming {model_name} ({label}) ...")
    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=(15, 600),
            stream=True,
        ) as r:
            if not r.ok:
                log(f"FAILED {model_name}: HTTP {r.status_code} {r.text[:160]}")
                return False
            for raw in r.iter_lines(chunk_size=1):
                if raw:
                    break
        dt = time.time() - t0
        log(f"READY   {model_name} in {dt:.1f}s (weights + KV cache pinned)")
        return True
    except Exception as exc:
        log(f"ERROR   {model_name}: {exc}")
        return False


def run_warm_cycle(warm_all_installed: bool = False) -> None:
    ram_gb = _host_ram_gb()
    installed = list_installed_models()
    log(f"Host RAM: {ram_gb} GB | Installed models: {installed or 'none'}")
    if not installed:
        log("No models installed in Ollama yet.")
        return

    targets = []
    if warm_all_installed:
        for m in installed:
            lbl = MODEL_LABEL if m.split(":")[0] == OLLAMA_MODEL.split(":")[0] else (
                "Unicollect Chat 1.2" if m.split(":")[0] == OLLAMA_MATH_MODEL.split(":")[0] else m
            )
            targets.append((m, lbl))
    else:
        # Warm 1.2 FIRST (populates weights & Linux page cache), then warm & pin Mini SECOND
        if OLLAMA_MATH_MODEL and OLLAMA_MATH_MODEL != OLLAMA_MODEL:
            if any(m.lower() == OLLAMA_MATH_MODEL.lower() or m.lower().split(":")[0] == OLLAMA_MATH_MODEL.lower().split(":")[0] for m in installed):
                targets.append((OLLAMA_MATH_MODEL, "Unicollect Chat 1.2"))
        targets.append((OLLAMA_MODEL, MODEL_LABEL))

    for model_name, label in targets:
        warm_model(model_name, label)

    loaded = _get_loaded_ollama_models()
    log(f"Currently hot in RAM (/api/ps): {loaded}")
    # Guarantee primary Mini model stays pinned if Ollama evicted it (e.g. OLLAMA_MAX_LOADED_MODELS=1)
    primary_base = OLLAMA_MODEL.split(":")[0].lower()
    if loaded and not any(m.split(":")[0].lower() == primary_base for m in loaded):
        log(
            f"NOTE: Ollama evicted {OLLAMA_MODEL} (daemon likely has OLLAMA_MAX_LOADED_MODELS=1). "
            f"Re-pinning {OLLAMA_MODEL} so default chat stays instant..."
        )
        warm_model(OLLAMA_MODEL, MODEL_LABEL)
        log(f"Final hot models (/api/ps): {_get_loaded_ollama_models()}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Warm up Unicollect Ollama models + KV cache.")
    ap.add_argument("--all", action="store_true", help="Warm ALL installed Ollama models")
    ap.add_argument("--watch", action="store_true", help="Keep checking every 45s and re-warm if unloaded")
    ap.add_argument("--timeout", type=int, default=120, help="Seconds to wait for Ollama startup")
    args = ap.parse_args()

    if not wait_for_ollama(args.timeout):
        return 1

    run_warm_cycle(warm_all_installed=args.all)
    if args.watch:
        log("Watch mode active: verifying hot models every 45s...")
        while True:
            time.sleep(45.0)
            try:
                if not _get_loaded_ollama_models():
                    log("Watchdog: 0 loaded models detected; re-warming...")
                    run_warm_cycle(warm_all_installed=args.all)
            except Exception as exc:
                log(f"Watchdog check error: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
