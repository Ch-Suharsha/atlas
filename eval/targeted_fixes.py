"""
3 targeted test cases for the 3 remaining deep_probe failures.
Run before the fix to confirm failures, after to confirm resolution.

  FIX-1: cancel follow-up on shipped order — reply must mention "return"
  FIX-2: order confirmation ("yes that's it") — reply must retain ORD number
  FIX-3: refund follow-up when order ID was in a separate prior message

Run: python3 eval/targeted_fixes.py 2>&1 | tee eval/targeted_fixes_results.txt
"""
import requests, uuid, time, textwrap

BASE = "http://localhost:8000"
issues_log = []

def sid():
    return f"fix-{uuid.uuid4().hex[:8]}"

def chat(session_id, message):
    t0 = time.time()
    r = requests.post(f"{BASE}/chat",
                      json={"session_id": session_id, "message": message},
                      timeout=90)
    return r.json(), round(time.time() - t0, 1)

def run(name, turns, note=""):
    s = sid()
    print(f"\n{'═'*80}")
    print(f"  SCENARIO: {name}")
    if note:
        print(f"  NOTE    : {note}")
    print(f"{'═'*80}")
    scenario_issues = []

    for i, (user_msg, hints) in enumerate(turns, 1):
        resp, lat = chat(s, user_msg)
        reply = resp.get("reply", "")
        tools = [t.get("name", "?") for t in resp.get("tools_called", [])]

        print(f"\n  ┌─ Turn {i}  ({lat}s)")
        print(f"  │  USER : {user_msg}")
        print(f"  │  TOOLS: {tools if tools else '[]'}")
        print(f"  └─ BOT  :")
        for line in textwrap.wrap(reply, 76):
            print(f"           {line}")

        issues = []
        if "expect_in_reply" in hints:
            for kw in hints["expect_in_reply"]:
                if kw.lower() not in reply.lower():
                    issues.append(f"Expected '{kw}' in reply but not found")
        if "expect_tool" in hints and hints["expect_tool"] not in tools:
            issues.append(f"Expected tool '{hints['expect_tool']}' not called (got {tools})")

        for iss in issues:
            print(f"\n  ⚠  {iss}")
            scenario_issues.append(f"T{i}: {iss}")
            issues_log.append((name, i, iss))

    print(f"\n  {'✓  No issues detected' if not scenario_issues else f'✗  {len(scenario_issues)} issue(s)'}")


# ── FIX-1: cancel follow-up on shipped order ─────────────────────────────────
# Root cause: post-processor at end of run_agent requires lookup_inv in current
# turn, but Safety Net 2 may return early; also history-based check was missing.
run("FIX-1: Cancel follow-up on shipped order must mention 'return'",
    note="T3 is a follow-up question about the failed cancel — bot must mention return path",
    turns=[
        ("My email is demo@atlas.local and order ORD-88210",
         {}),
        ("Can I cancel order ORD-88210?",
         {"expect_tool": "cancel_order"}),
        ("So I can't cancel it because it already shipped?",
         {"expect_in_reply": ["return"]}),
        ("How long is the return window?",
         {}),
    ])

# ── FIX-2: order confirmation carryforward ────────────────────────────────────
# Root cause: "Yes that's it — the Blue Wireless Headphones" had "wireless" in
# _PRODUCT_FOLLOWUP_RE and "headphone" in _PRODUCT_KEYWORDS but no order context
# pattern, so lookup_order was never called and ORD-88210 wasn't in the reply.
run("FIX-2: Confirming order contents must retain ORD number in reply",
    note="T3 confirms 'yes that's it' after the bot found ORD-88210 — ORD must appear in reply",
    turns=[
        ("My email is demo@atlas.local",
         {}),
        ("My order is ORD-88210",
         {"expect_tool": "lookup_order"}),
        ("Yes that's it — the Blue Wireless Headphones",
         {"expect_in_reply": ["ORD-88210"]}),
        ("When exactly does it arrive?",
         {"expect_in_reply": ["2026-05-08"]}),
    ])

# ── FIX-3: refund follow-up when order ID was in a separate prior turn ────────
# Root cause: _extract_prior_refund_order_id searched only messages that had
# BOTH a refund keyword AND an order ID — but the template reply only has Refund ID,
# not ORD-XXXXX, and the user's refund message had no ORD ID either (it was in T2).
run("FIX-3: Refund status follow-up must mention 'refund' even across separate turns",
    note="Order ID given in T2, refund requested in T3; T4 follow-up must get refund context",
    turns=[
        ("My email is demo@atlas.local",
         {}),
        ("My order number is ORD-88210",
         {"expect_tool": "lookup_order"}),
        ("Please process a refund for that order",
         {"expect_tool": "process_refund"}),
        ("Has my refund been confirmed?",
         {"expect_in_reply": ["refund"]}),
        ("How long will it take to appear on my bank statement?",
         {"expect_in_reply": ["refund"]}),
    ])


print(f"\n\nTotal issues: {len(issues_log)} across "
      f"{len({s for s,_,_ in issues_log})} scenario(s)")
