"""
Atlas Evaluation Script
=======================
Compares two configurations:
  A) Fine-tuned Phi-4-mini + RAG  (current system via /chat endpoint)
  B) Fine-tuned Phi-4-mini alone  (same HF endpoint, no RAG context injected)

Metrics:
  - G-Eval via Gemini 2.5 Flash (5 dimensions, 1-5 scale)
  - ROUGE-L
  - BERTScore (optional — skipped if package missing)
  - Task Success Rate (key facts present in reply)

Usage:
  pip install rouge-score requests google-genai
  python evaluate.py --gemini-key YOUR_KEY
  python evaluate.py --gemini-key YOUR_KEY --out results.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests

# ── optional imports ────────────────────────────────────────────────
try:
    from rouge_score import rouge_scorer as rouge_lib
    HAS_ROUGE = True
except ImportError:
    HAS_ROUGE = False
    print("[warn] rouge-score not installed — ROUGE-L will be skipped")

try:
    from google import genai as google_genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("[warn] google-genai not installed — G-Eval will be skipped")

try:
    from bert_score import score as bert_score_fn
    HAS_BERT = True
except ImportError:
    HAS_BERT = False


# ── Config ──────────────────────────────────────────────────────────
CHAT_ENDPOINT   = os.getenv("ATLAS_ENDPOINT", "http://localhost:8000/chat")
HF_ENDPOINT_URL = os.getenv("HF_ENDPOINT_URL", "")
HF_TOKEN        = os.getenv("HF_TOKEN", "")
GEMINI_MODEL    = "gemini-2.5-flash"

SYSTEM_PROMPT = (
    "You are Atlas, a warm, direct, and helpful customer support representative "
    "for our e-commerce platform. Keep replies concise and to the point."
)

G_EVAL_DIMENSIONS = [
    ("relevance",    "Does the response directly address the customer's question? (1=completely off-topic, 5=perfectly on-topic)"),
    ("faithfulness", "Does the response stick to factual system data without hallucinating? (1=makes things up, 5=only states verified facts)"),
    ("completeness", "Does the response fully answer what was asked, without missing key information? (1=missing most info, 5=complete answer)"),
    ("tone",         "Is the tone warm, professional, and appropriate for customer support? (1=rude or robotic, 5=warm and natural)"),
    ("groundedness", "For RAG: does the answer use the specific retrieved data correctly? For no-RAG: does it avoid making up specific values? (1=fabricates data, 5=correct usage)"),
]

SLEEP_BETWEEN = 1.5


# ── Helpers ─────────────────────────────────────────────────────────

def load_test_cases(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def call_atlas_rag(tc: dict, session_id: str) -> dict:
    """Call the full Atlas system (fine-tuned + RAG).
    Passes customer_id from the test case when present so authenticated cases
    bypass the identity gate and exercise the actual retrieval + LLM pipeline.
    """
    payload: dict = {"session_id": session_id, "message": tc["question"]}
    if tc.get("customer_id"):
        payload["customer_id"] = tc["customer_id"]
    try:
        r = requests.post(CHAT_ENDPOINT, json=payload, timeout=90)
        r.raise_for_status()
        d = r.json()
        return {
            "reply": d.get("reply", ""),
            "tools": [t["name"] if isinstance(t, dict) else str(t)
                      for t in d.get("tools_called", [])],
            "error": None,
        }
    except Exception as e:
        return {"reply": "", "tools": [], "error": str(e)}


def call_hf_no_rag(tc: dict) -> dict:
    """Call the fine-tuned HF endpoint directly — no RAG context injected."""
    if not HF_ENDPOINT_URL or not HF_TOKEN:
        return {"reply": "[HF_ENDPOINT_URL or HF_TOKEN not set]", "tools": [], "error": "missing config"}

    prompt = (
        f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"
        f"<|user|>\n{tc['question']}<|end|>\n"
        f"<|assistant|>"
    )
    for attempt in range(3):
        try:
            r = requests.post(
                HF_ENDPOINT_URL,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 300,
                        "temperature": 0.1,
                        "return_full_text": False,
                    },
                },
                timeout=90,
            )
            r.raise_for_status()
            result = r.json()
            text = result[0].get("generated_text", "") if isinstance(result, list) else result.get("generated_text", "")
            return {"reply": text.strip(), "tools": [], "error": None}
        except Exception as e:
            if attempt < 2:
                time.sleep(12)
            else:
                return {"reply": "", "tools": [], "error": str(e)}
    return {"reply": "", "tools": [], "error": "max retries"}


def rouge_l(hypothesis: str, reference: str) -> float:
    if not HAS_ROUGE or not hypothesis or not reference:
        return 0.0
    scorer = rouge_lib.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return round(scores["rougeL"].fmeasure, 4)


def task_success(tc: dict, result: dict) -> float:
    reply_lower = result["reply"].lower()
    if not tc.get("key_facts"):
        return 1.0
    hits = sum(1 for kf in tc["key_facts"] if kf.lower() in reply_lower)
    return round(hits / len(tc["key_facts"]), 2)


def g_eval_score(
    gemini_client,
    question: str,
    ideal: str,
    response: str,
    variant_label: str,
) -> dict[str, float]:
    if not HAS_GEMINI or gemini_client is None:
        return {dim: 0.0 for dim, _ in G_EVAL_DIMENSIONS}

    scores = {}
    for dim_name, dim_desc in G_EVAL_DIMENSIONS:
        prompt = f"""You are an expert evaluator for customer support AI systems.

Evaluate the following AI response on the dimension: **{dim_name}**
Criterion: {dim_desc}

Customer Question:
{question}

Reference ideal answer (for context only):
{ideal}

AI Response ({variant_label}):
{response}

Instructions:
- Score from 1 to 5 (integers only).
- Reply with ONLY a single integer between 1 and 5.
- Do not explain."""

        try:
            result = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            raw = result.text.strip()
            match = re.search(r"[1-5]", raw)
            scores[dim_name] = float(match.group()) if match else 0.0
        except Exception as e:
            print(f"    [g-eval error] {dim_name}: {e}")
            scores[dim_name] = 0.0
        time.sleep(0.5)

    return scores


def g_eval_average(scores: dict[str, float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores.values()) / len(scores), 2)


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="test_cases.json")
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY", ""))
    parser.add_argument("--out", default="results.md")
    parser.add_argument("--limit", type=int, default=0, help="Run only first N cases (0 = all)")
    args = parser.parse_args()

    cases = load_test_cases(args.cases)
    if args.limit:
        cases = cases[: args.limit]

    gemini_client = None
    if HAS_GEMINI and args.gemini_key:
        gemini_client = google_genai.Client(api_key=args.gemini_key)
        print(f"[info] Gemini judge ready ({GEMINI_MODEL})")
    else:
        print("[warn] Gemini judge not available — G-Eval scores will be 0")

    hf_available = bool(HF_ENDPOINT_URL and HF_TOKEN)
    if not hf_available:
        print("[warn] HF_ENDPOINT_URL or HF_TOKEN not set — Fine-tuned-only variant will be skipped")

    print(f"\nRunning evaluation on {len(cases)} test cases...\n")

    rows = []

    for i, tc in enumerate(cases):
        print(f"  [{i+1:02d}/{len(cases)}] {tc['id']} — {tc['category']} — {tc['question'][:60]}")

        session_rag = f"eval-rag-{tc['id']}-{int(time.time())}"

        # ── Variant A: Fine-tuned + RAG ──────────────────────────────
        res_rag = call_atlas_rag(tc, session_rag)
        time.sleep(SLEEP_BETWEEN)

        # ── Variant B: Fine-tuned, no RAG ────────────────────────────
        res_norag = call_hf_no_rag(tc) if hf_available else {"reply": "", "tools": [], "error": "skipped"}
        time.sleep(SLEEP_BETWEEN)

        if res_rag["error"]:
            print(f"    [!] RAG call failed: {res_rag['error']}")
        if res_norag["error"] and res_norag["error"] != "skipped":
            print(f"    [!] No-RAG call failed: {res_norag['error']}")

        ideal = tc.get("ideal_answer", "")

        rouge_rag   = rouge_l(res_rag["reply"],   ideal)
        rouge_norag = rouge_l(res_norag["reply"],  ideal)

        ts_rag   = task_success(tc, res_rag)
        ts_norag = task_success(tc, res_norag)

        geval_rag   = g_eval_score(gemini_client, tc["question"], ideal, res_rag["reply"],   "Fine-tuned + RAG")
        geval_norag = g_eval_score(gemini_client, tc["question"], ideal, res_norag["reply"],  "Fine-tuned, no RAG") if hf_available else {d: 0.0 for d, _ in G_EVAL_DIMENSIONS}

        rows.append({
            "tc":           tc,
            "res_rag":      res_rag,
            "res_norag":    res_norag,
            "rouge_rag":    rouge_rag,
            "rouge_norag":  rouge_norag,
            "ts_rag":       ts_rag,
            "ts_norag":     ts_norag,
            "geval_rag":    geval_rag,
            "geval_norag":  geval_norag,
        })

        print(f"    ROUGE-L  RAG={rouge_rag:.3f}  NoRAG={rouge_norag:.3f}")
        print(f"    Task-SR  RAG={ts_rag:.2f}    NoRAG={ts_norag:.2f}")
        if geval_rag:
            print(f"    G-Eval   RAG={g_eval_average(geval_rag):.2f}   NoRAG={g_eval_average(geval_norag):.2f}")

    # ── Aggregate ────────────────────────────────────────────────────
    def avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    agg = {
        "rouge_rag":   avg([r["rouge_rag"]  for r in rows]),
        "rouge_norag": avg([r["rouge_norag"] for r in rows]),
        "ts_rag":      avg([r["ts_rag"]     for r in rows]),
        "ts_norag":    avg([r["ts_norag"]   for r in rows]),
        "geval_rag":   avg([g_eval_average(r["geval_rag"])   for r in rows]),
        "geval_norag": avg([g_eval_average(r["geval_norag"]) for r in rows]),
    }

    dim_agg = {}
    for dim_name, _ in G_EVAL_DIMENSIONS:
        dim_agg[dim_name] = {
            "rag":   avg([r["geval_rag"].get(dim_name, 0)   for r in rows]),
            "norag": avg([r["geval_norag"].get(dim_name, 0) for r in rows]),
        }

    cats = sorted(set(r["tc"]["category"] for r in rows))
    cat_agg = {}
    for cat in cats:
        cat_rows = [r for r in rows if r["tc"]["category"] == cat]
        cat_agg[cat] = {
            "n":           len(cat_rows),
            "ts_rag":      avg([r["ts_rag"]   for r in cat_rows]),
            "ts_norag":    avg([r["ts_norag"] for r in cat_rows]),
            "geval_rag":   avg([g_eval_average(r["geval_rag"])   for r in cat_rows]),
            "geval_norag": avg([g_eval_average(r["geval_norag"]) for r in cat_rows]),
        }

    write_report(rows, agg, dim_agg, cat_agg, args.out, hf_available)
    print(f"\n[done] Report written to {args.out}")
    print(f"\n{'='*60}")
    print(f"  OVERALL SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Metric':<25} {'Fine-tuned+RAG':>16}  {'Fine-tuned only':>16}")
    print(f"  {'-'*59}")
    print(f"  {'ROUGE-L':<25} {agg['rouge_rag']:>16.3f}  {agg['rouge_norag']:>16.3f}")
    print(f"  {'Task Success Rate':<25} {agg['ts_rag']:>16.3f}  {agg['ts_norag']:>16.3f}")
    print(f"  {'G-Eval (avg 1-5)':<25} {agg['geval_rag']:>16.2f}  {agg['geval_norag']:>16.2f}")
    print(f"{'='*60}")


def write_report(rows, agg, dim_agg, cat_agg, out_path: str, hf_available: bool = True):
    lines = []
    a = lines.append

    a("# Atlas Model Evaluation Report")
    a("")
    a(f"> Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    a(f"> Test cases: {len(rows)}")
    a(f"> Configurations compared:")
    a(f">   - **A** — Fine-tuned Phi-4-mini + RAG (full system)")
    a(f">   - **B** — Fine-tuned Phi-4-mini, no RAG (same model, no retrieved context)")
    if not hf_available:
        a(f">")
        a(f"> ⚠️  Variant B (no-RAG) was skipped — HF endpoint not configured.")
    a("")
    a("---")
    a("")

    # ── Overall summary ──────────────────────────────────────────────
    a("## Overall Results")
    a("")
    a("| Metric | Fine-tuned + RAG | Fine-tuned only | Delta |")
    a("|--------|:---------------:|:---------------:|:-----:|")

    def delta(a_val, b_val):
        d = a_val - b_val
        return f"+{d:.3f}" if d >= 0 else f"{d:.3f}"

    a(f"| ROUGE-L | {agg['rouge_rag']:.3f} | {agg['rouge_norag']:.3f} | {delta(agg['rouge_rag'], agg['rouge_norag'])} |")
    a(f"| Task Success Rate | {agg['ts_rag']:.3f} | {agg['ts_norag']:.3f} | {delta(agg['ts_rag'], agg['ts_norag'])} |")
    a(f"| G-Eval (avg 1–5) | {agg['geval_rag']:.2f} | {agg['geval_norag']:.2f} | {delta(agg['geval_rag'], agg['geval_norag'])} |")
    a("")

    # ── G-Eval per dimension ─────────────────────────────────────────
    a("## G-Eval Breakdown (per dimension, 1–5 scale)")
    a("")
    a("| Dimension | Fine-tuned + RAG | Fine-tuned only | Delta |")
    a("|-----------|:---------------:|:---------------:|:-----:|")
    for dim_name, label in [
        ("relevance",    "Relevance"),
        ("faithfulness", "Faithfulness"),
        ("completeness", "Completeness"),
        ("tone",         "Tone & Empathy"),
        ("groundedness", "Groundedness"),
    ]:
        d = dim_agg.get(dim_name, {"rag": 0.0, "norag": 0.0})
        a(f"| {label} | {d['rag']:.2f} | {d['norag']:.2f} | {delta(d['rag'], d['norag'])} |")
    a("")

    # ── Per category ─────────────────────────────────────────────────
    a("## Results by Category")
    a("")
    a("| Category | N | Task-SR (RAG) | Task-SR (no RAG) | G-Eval (RAG) | G-Eval (no RAG) |")
    a("|----------|:-:|:-------------:|:----------------:|:------------:|:---------------:|")
    for cat, cv in cat_agg.items():
        a(f"| {cat} | {cv['n']} | {cv['ts_rag']:.2f} | {cv['ts_norag']:.2f} | {cv['geval_rag']:.2f} | {cv['geval_norag']:.2f} |")
    a("")

    # ── Per-case detail ──────────────────────────────────────────────
    a("## Per-Case Detail")
    a("")
    for r in rows:
        tc = r["tc"]
        a(f"### {tc['id']} — {tc['category']}")
        a(f"**Question:** {tc['question']}")
        a(f"**Requires RAG:** {'Yes' if tc['requires_rag'] else 'No'}")
        a("")
        a("**Response A — Fine-tuned + RAG:**")
        reply_a = r['res_rag']['reply']
        a(f"> {reply_a[:500].replace(chr(10), ' ') if reply_a else '_[no response]_'}")
        if r['res_rag']['tools']:
            a(f"> *Tools fired:* `{', '.join(r['res_rag']['tools'])}`")
        a("")
        a("**Response B — Fine-tuned, no RAG:**")
        reply_b = r['res_norag']['reply']
        a(f"> {reply_b[:500].replace(chr(10), ' ') if reply_b else '_[skipped or no response]_'}")
        a("")
        a("| Metric | RAG | No RAG |")
        a("|--------|:---:|:------:|")
        a(f"| ROUGE-L | {r['rouge_rag']:.3f} | {r['rouge_norag']:.3f} |")
        a(f"| Task Success | {r['ts_rag']:.2f} | {r['ts_norag']:.2f} |")
        if r['geval_rag']:
            for dim_name, label in [
                ("relevance",    "Relevance"),
                ("faithfulness", "Faithfulness"),
                ("completeness", "Completeness"),
                ("tone",         "Tone & Empathy"),
                ("groundedness", "Groundedness"),
            ]:
                a(f"| G-Eval {label} | {r['geval_rag'].get(dim_name, 0):.1f} | {r['geval_norag'].get(dim_name, 0):.1f} |")
            a(f"| **G-Eval avg** | **{g_eval_average(r['geval_rag']):.2f}** | **{g_eval_average(r['geval_norag']):.2f}** |")
        a("")
        a("---")
        a("")

    # ── Methodology ──────────────────────────────────────────────────
    a("## Evaluation Methodology")
    a("")
    a("### Metrics")
    a("")
    a("| Metric | Description |")
    a("|--------|-------------|")
    a("| **ROUGE-L** | Longest common subsequence overlap between generated response and ideal answer. Measures surface-level text similarity. Range 0–1, higher is better. |")
    a("| **Task Success Rate** | Fraction of key facts (order IDs, tracking numbers, policy keywords) that appear in the response. Measures whether the answer is factually grounded. Range 0–1, higher is better. |")
    a(f"| **G-Eval (Gemini judge)** | LLM-as-judge scoring across 5 dimensions on a 1–5 scale. Judge model: {GEMINI_MODEL}. Each dimension scored independently with a structured prompt. |")
    a("")
    a("### G-Eval Dimensions")
    a("")
    for dim_name, dim_desc in G_EVAL_DIMENSIONS:
        a(f"- **{dim_name.capitalize()}**: {dim_desc}")
    a("")
    a("### Configurations")
    a("")
    a("- **Fine-tuned + RAG**: Full Atlas system. User message → deterministic tool routing (order lookup, policy search, product search) → context injection → Phi-4-mini fine-tuned endpoint.")
    a("- **Fine-tuned, no RAG**: Same fine-tuned Phi-4-mini endpoint called directly with only the system prompt and user message. No retrieved context injected.")
    a("")
    a("### Test Set")
    a("")
    a("50 hand-crafted test cases across 7 categories:")
    a("- Order lookup (10 cases) — authenticated via `customer_id` to bypass identity gate")
    a("- Refund requests (7 cases)")
    a("- Cancellation (3 cases)")
    a("- Policy questions (12 cases)")
    a("- Product recommendations (10 cases)")
    a("- Account information (5 cases) — authenticated via `customer_id`")
    a("- Escalation (3 cases)")
    a("")

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
