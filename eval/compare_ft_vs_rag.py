"""
Fine-tuned (no RAG) vs Fine-tuned + RAG comparison eval.
Uses 50 test cases from eval_test_cases.py.

  Fine-tuned only  : calls the HF inference endpoint directly (no tool execution, no RAG)
  Fine-tuned + RAG : calls the deployed API at http://localhost:8000/chat

Run:
    python3 eval/compare_ft_vs_rag.py 2>&1 | tee eval/ft_vs_rag_results.txt
"""

import os, sys, uuid, time, json, re, requests
from statistics import mean, median
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eval_test_cases import TEST_CASES, score_response

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE        = "http://localhost:8000"
HF_ENDPOINT_URL = os.getenv("HF_ENDPOINT_URL", "https://tbc9nz0g0fw10hsb.eu-west-1.aws.endpoints.huggingface.cloud")
HF_TOKEN        = os.getenv("HF_TOKEN", "")

SYSTEM_PROMPT = (
    "You are Atlas, a warm, direct, and helpful customer support representative "
    "for our e-commerce platform. You resolve shopping inquiries using verified "
    "system data. Keep replies concise and to the point."
)

PHI4_STOP = ["<|end|>", "<|user|>", "<|system|>"]


# ── Callers ────────────────────────────────────────────────────────────────────

def call_finetuned_rag(message: str) -> tuple[str, list, float]:
    """Call the full deployed system (fine-tuned + RAG + tools)."""
    session_id = f"eval-rag-{uuid.uuid4().hex[:8]}"
    t0 = time.time()
    try:
        r = requests.post(
            f"{API_BASE}/chat",
            json={"session_id": session_id, "message": message},
            timeout=90,
        )
        data = r.json()
        reply = data.get("reply", "")
        tools = [t.get("name", "") for t in data.get("tools_called", [])]
        return reply, tools, round(time.time() - t0, 2)
    except Exception as e:
        return f"[ERROR: {e}]", [], round(time.time() - t0, 2)


def call_finetuned_only(message: str) -> tuple[str, float]:
    """Call the fine-tuned HF endpoint directly — no RAG, no tools, no DB."""
    prompt = (
        f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"
        f"<|user|>\n{message}<|end|>\n"
        f"<|assistant|>\n"
    )
    t0 = time.time()
    if not HF_TOKEN:
        return "[ERROR: HF_TOKEN not set]", 0.0
    try:
        r = requests.post(
            HF_ENDPOINT_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 256,
                    "temperature": 0.1,
                    "return_full_text": False,
                    "stop": PHI4_STOP,
                },
            },
            timeout=90,
        )
        result = r.json()
        if isinstance(result, list):
            text = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            text = result.get("generated_text", result.get("error", "[no output]"))
        else:
            text = str(result)
        # Strip any residual stop tokens
        for tok in PHI4_STOP:
            text = text.replace(tok, "").strip()
        return text, round(time.time() - t0, 2)
    except Exception as e:
        return f"[ERROR: {e}]", round(time.time() - t0, 2)


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_eval():
    ft_results  = []
    rag_results = []

    policy_cases      = [tc for tc in TEST_CASES if tc["category"] == "policy"]
    behavioral_cases  = [tc for tc in TEST_CASES if tc["category"] == "behavioral"]
    operational_cases = [tc for tc in TEST_CASES if tc["category"] == "operational"]

    print("=" * 72)
    print("  ATLAS EVAL: Fine-tuned (no RAG)  vs  Fine-tuned + RAG")
    print(f"  {len(TEST_CASES)} test cases  |  {len(policy_cases)} policy  "
          f"|  {len(behavioral_cases)} behavioral  |  {len(operational_cases)} operational")
    print("=" * 72)

    # ── Policy + behavioral: run against BOTH systems ──────────────────────────
    comparable_cases = policy_cases + behavioral_cases
    print(f"\n[1/2] Running {len(comparable_cases)} comparable cases against both systems...\n")

    for i, tc in enumerate(comparable_cases, 1):
        print(f"  [{i:02d}/{len(comparable_cases):02d}] {tc['id']}  {tc['message'][:55]}...")

        # Fine-tuned only
        ft_reply, ft_lat = call_finetuned_only(tc["message"])
        ft_score = score_response(ft_reply, tc, tools_called=None, latency=ft_lat)
        ft_score["full_reply"] = ft_reply
        ft_results.append(ft_score)

        # Fine-tuned + RAG
        rag_reply, rag_tools, rag_lat = call_finetuned_rag(tc["message"])
        rag_score = score_response(rag_reply, tc, tools_called=rag_tools, latency=rag_lat)
        rag_score["full_reply"] = rag_reply
        rag_score["tools_called"] = rag_tools
        rag_results.append(rag_score)

        c_sym  = "✓" if ft_score["compliance_score"] >= 0.75 else "✗"
        r_sym  = "✓" if rag_score["compliance_score"] >= 0.75 else "✗"
        print(f"         FT  compliance={ft_score['compliance_score']:.2f}  "
              f"specificity={ft_score['policy_specificity']}  "
              f"relevance={ft_score['response_relevance']}  "
              f"lat={ft_lat}s  {c_sym}")
        print(f"         RAG compliance={rag_score['compliance_score']:.2f}  "
              f"specificity={rag_score['policy_specificity']}  "
              f"relevance={rag_score['response_relevance']}  "
              f"lat={rag_lat}s  {r_sym}")

    # ── Operational: run against fine-tuned+RAG only ───────────────────────────
    print(f"\n[2/2] Running {len(operational_cases)} operational cases (fine-tuned+RAG only)...\n")

    rag_ops_results = []
    for i, tc in enumerate(operational_cases, 1):
        print(f"  [{i:02d}/{len(operational_cases):02d}] {tc['id']}  {tc['message'][:55]}...")
        rag_reply, rag_tools, rag_lat = call_finetuned_rag(tc["message"])
        rag_score = score_response(rag_reply, tc, tools_called=rag_tools, latency=rag_lat)
        rag_score["full_reply"] = rag_reply
        rag_score["tools_called"] = rag_tools
        rag_ops_results.append(rag_score)

        tool_ok = "✓" if rag_score["tool_correct"] else "✗"
        print(f"         tools={rag_tools}  relevance={rag_score['response_relevance']}  "
              f"tool_correct={tool_ok}  lat={rag_lat}s")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  RESULTS SUMMARY")
    print("=" * 72)

    def avg(lst, key):
        vals = [r[key] for r in lst if r[key] is not None]
        return round(mean(vals), 3) if vals else None

    def pct(lst, key):
        vals = [r[key] for r in lst if r[key] is not None]
        return round(mean(int(v) for v in vals), 3) if vals else None

    policy_ft  = [r for r in ft_results  if r["category"] == "policy"]
    policy_rag = [r for r in rag_results if r["category"] == "policy"]
    beh_ft     = [r for r in ft_results  if r["category"] == "behavioral"]
    beh_rag    = [r for r in rag_results if r["category"] == "behavioral"]

    print(f"\n{'Metric':<35} {'FT (no RAG)':>14} {'FT + RAG':>14}")
    print("-" * 65)

    # Policy questions
    print("\n  ── Policy Questions ──")
    for label, key, fmt in [
        ("Compliance Rate",        "compliance_score",   ".3f"),
        ("Policy Specificity",     "policy_specificity", ".3f"),
        ("Response Relevance",     "response_relevance", ".3f"),
        ("Hallucination Rate",     "hallucination",      ".3f"),
        ("Latency p50 (s)",        "latency_s",          ".2f"),
    ]:
        ft_val  = avg(policy_ft,  key) if key != "hallucination" else pct(policy_ft,  key)
        rag_val = avg(policy_rag, key) if key != "hallucination" else pct(policy_rag, key)
        ft_str  = f"{ft_val:{fmt}}"  if ft_val  is not None else "  N/A"
        rag_str = f"{rag_val:{fmt}}" if rag_val is not None else "  N/A"
        print(f"  {label:<33} {ft_str:>14} {rag_str:>14}")

    # Behavioral
    print("\n  ── Behavioral / Compliance ──")
    for label, key, fmt in [
        ("Compliance Rate",    "compliance_score",   ".3f"),
        ("Empathy Rate",       "has_empathy",        ".3f"),
        ("Next-Step Rate",     "has_next_step",      ".3f"),
        ("Hallucination Rate", "hallucination",      ".3f"),
        ("Latency p50 (s)",    "latency_s",          ".2f"),
    ]:
        ft_val  = avg(beh_ft,  key) if key not in ("has_empathy","has_next_step","hallucination") \
                  else pct(beh_ft,  key)
        rag_val = avg(beh_rag, key) if key not in ("has_empathy","has_next_step","hallucination") \
                  else pct(beh_rag, key)
        ft_str  = f"{ft_val:{fmt}}"  if ft_val  is not None else "  N/A"
        rag_str = f"{rag_val:{fmt}}" if rag_val is not None else "  N/A"
        print(f"  {label:<33} {ft_str:>14} {rag_str:>14}")

    # Operational (RAG only)
    print("\n  ── Operational (fine-tuned+RAG only) ──")
    tool_acc = mean(int(r["tool_correct"]) for r in rag_ops_results if r["tool_correct"] is not None)
    rel_acc  = mean(r["response_relevance"] for r in rag_ops_results)
    lat_med  = median(r["latency_s"] for r in rag_ops_results if r["latency_s"])
    print(f"  {'Tool Call Accuracy':<33} {'N/A':>14} {tool_acc:>14.3f}")
    print(f"  {'Response Relevance':<33} {'N/A':>14} {rel_acc:>14.3f}")
    print(f"  {'Latency p50 (s)':<33} {'N/A':>14} {lat_med:>14.2f}")

    # FCR breakdown
    print("\n  ── FCR Classification (policy + behavioral) ──")
    for label, results in [("FT (no RAG)", ft_results), ("FT + RAG", rag_results)]:
        total = len(results)
        resolved   = sum(1 for r in results if r["fcr"] == "resolved")
        escalated  = sum(1 for r in results if r["fcr"] == "escalated")
        followup   = sum(1 for r in results if r["fcr"] == "needs_followup")
        print(f"  {label}: resolved={resolved/total:.2f}  "
              f"escalated={escalated/total:.2f}  follow-up={followup/total:.2f}")

    # ── Save JSON ──────────────────────────────────────────────────────────────
    output = {
        "finetuned_only":    ft_results,
        "finetuned_rag":     rag_results,
        "operational_rag":   rag_ops_results,
    }
    out_path = Path(__file__).parent / "ft_vs_rag_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\n  Raw results saved → {out_path}")
    print("=" * 72)

    # ── Side-by-side examples ──────────────────────────────────────────────────
    print("\n\n  SIDE-BY-SIDE EXAMPLES (policy questions with largest specificity gap)\n")
    paired = list(zip(
        [r for r in ft_results  if r["category"] == "policy"],
        [r for r in rag_results if r["category"] == "policy"],
    ))
    paired.sort(key=lambda x: (x[1]["policy_specificity"] or 0) - (x[0]["policy_specificity"] or 0), reverse=True)
    for ft_r, rag_r in paired[:5]:
        print(f"  ┌─ {ft_r['id']}: {ft_r['message']}")
        print(f"  │  FT  (specificity={ft_r['policy_specificity']}): {ft_r['reply_preview']}")
        print(f"  │  RAG (specificity={rag_r['policy_specificity']}): {rag_r['reply_preview']}")
        print()


if __name__ == "__main__":
    run_eval()
