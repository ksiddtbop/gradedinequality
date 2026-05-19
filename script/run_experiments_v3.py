#!/usr/bin/env python3
"""
EquiCaste v3 lean runner.

Reads scenarios_v3.csv (situation_id, prompt_template), sends each prompt
once per model at temperature 0.0, and writes results to a resumable JSONL.

Per model: 10 scenarios -> 10 outputs.
Across the four models: 40 outputs total.

Both names are already hardcoded in each prompt — no substitution layer.

Usage:
  # Dry-run: confirm the prompt set without any API calls
  python run_experiments_v3.py --dry-run --out runs/

  # Live:
  OPENAI_API_KEY=...    python run_experiments_v3.py --model gpt-4o --out runs/
  ANTHROPIC_API_KEY=... python run_experiments_v3.py --model claude --out runs/
  GOOGLE_API_KEY=...    python run_experiments_v3.py --model gemini --out runs/
  GROQ_API_KEY=...      python run_experiments_v3.py --model llama  --out runs/
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

MODEL_VERSIONS = {
    "gpt-4o":  os.environ.get("MODEL_VERSION_GPT4O",  "gpt-4o-2024-08-06"),
    "claude":  os.environ.get("MODEL_VERSION_CLAUDE", "claude-sonnet-4-5-20250929"),
    "gemini":  os.environ.get("MODEL_VERSION_GEMINI", "gemini-2.0-flash"),
    "llama":   os.environ.get("MODEL_VERSION_LLAMA",  "llama-3.3-70b-versatile"),
}

TEMPERATURE = 0.0
MAX_TOKENS  = 2000


# --- Model adapters -------------------------------------------------------

def call_gpt4o(prompt, version):
    from openai import OpenAI
    client = OpenAI()
    r = client.chat.completions.create(
        model=version, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content or "", r.model_dump()

def call_claude(prompt, version):
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=version, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
        messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in r.content if b.type == "text"), r.model_dump()

def call_gemini(prompt, version):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    m = genai.GenerativeModel(version)
    r = m.generate_content(prompt, generation_config={
        "temperature": TEMPERATURE, "max_output_tokens": MAX_TOKENS})
    return r.text or "", {"text": r.text}

def call_llama(prompt, version):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["GROQ_API_KEY"],
                    base_url="https://api.groq.com/openai/v1")
    r = client.chat.completions.create(
        model=version, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content or "", r.model_dump()

CALLERS = {"gpt-4o": call_gpt4o, "claude": call_claude,
           "gemini": call_gemini, "llama": call_llama}


# --- Pipeline -------------------------------------------------------------

def load_scenarios(path):
    with open(path) as f:
        return list(csv.DictReader(f))

def load_done(jsonl_path):
    if not jsonl_path.exists():
        return set()
    done = set()
    with open(jsonl_path) as f:
        for line in f:
            try:
                r = json.loads(line)
                if r.get("error") is None:
                    done.add(r["situation_id"])
            except json.JSONDecodeError:
                pass
    return done

def run(args):
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    scenarios = load_scenarios(args.scenarios)
    print(f"[setup] {len(scenarios)} scenarios loaded from {args.scenarios}")

    if args.dry_run:
        dump = out_dir / "prompts_v3.jsonl"
        with open(dump, "w") as f:
            for s in scenarios:
                f.write(json.dumps(s) + "\n")
        print(f"[dry-run] wrote -> {dump}")
        return

    if args.model not in CALLERS:
        sys.exit(f"unknown model: {args.model}. choose from {list(CALLERS)}")

    out_path = out_dir / f"results_v3_{args.model}.jsonl"
    done     = load_done(out_path)
    print(f"[resume] {len(done)}/{len(scenarios)} already complete")

    caller, version = CALLERS[args.model], MODEL_VERSIONS[args.model]
    with open(out_path, "a", buffering=1) as f:
        for s in scenarios:
            sid = s["situation_id"]
            if sid in done:
                continue
            start, error, text, raw = time.time(), None, "", {}
            for attempt in range(args.max_retries):
                try:
                    text, raw = caller(s["prompt_template"], version)
                    break
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
                    if attempt == args.max_retries - 1:
                        error = err
                        traceback.print_exc(file=sys.stderr)
                    else:
                        time.sleep(2 ** attempt)
            elapsed = time.time() - start
            row = {
                "situation_id":   sid,
                "model_key":      args.model,
                "model_version":  version,
                "temperature":    TEMPERATURE,
                "prompt":         s["prompt_template"],
                "response_text":  text,
                "response_raw":   raw,
                "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": elapsed,
                "error":          error,
            }
            f.write(json.dumps(row, default=str) + "\n")
            tag = "ERR" if error else "OK "
            print(f"[{tag}] {sid}  {elapsed:.1f}s  ({len(text)} chars)")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--scenarios", default="scenarios_v3.csv")
    p.add_argument("--out",       default="runs")
    p.add_argument("--model",     choices=list(CALLERS))
    p.add_argument("--dry-run",   action="store_true")
    p.add_argument("--max-retries", type=int, default=4)
    return p.parse_args()

if __name__ == "__main__":
    run(parse_args())
