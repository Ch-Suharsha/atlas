"""
15 new deep multi-turn scenarios — 10-12 turns each.
Covers angles not in the original convo_probe.py suite.

Run: python3 eval/deep_probe.py 2>&1 | tee eval/deep_probe_results.txt
"""
import requests, uuid, time, textwrap

BASE = "http://localhost:8000"

def sid():
    return f"deep-{uuid.uuid4().hex[:10]}"

issues_log = []

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
    prev_verified = False

    for i, (user_msg, hints) in enumerate(turns, 1):
        resp, lat = chat(s, user_msg)
        reply  = resp.get("reply", "")
        intent = resp.get("intent", "")
        sent   = resp.get("sentiment", "")
        esc    = resp.get("escalated", False)
        ver    = resp.get("customer_verified", False)
        tools  = [t.get("name", "?") for t in resp.get("tools_called", [])]

        print(f"\n  ┌─ Turn {i:2d}  ({lat}s)  intent={intent}  sent={sent}  "
              f"esc={esc}  ver={ver}")
        print(f"  │  USER : {user_msg}")
        print(f"  │  TOOLS: {tools if tools else '[]'}")
        print(f"  └─ BOT  :")
        for line in textwrap.wrap(reply, 76):
            print(f"           {line}")

        issues = []
        if "expect_tool" in hints and hints["expect_tool"] not in tools:
            issues.append(f"Expected tool '{hints['expect_tool']}' not called (got {tools})")
        if "expect_no_id_gate" in hints and hints["expect_no_id_gate"]:
            gate_phrases = ["verify your identity", "email address on your account",
                            "to look up your order", "need to verify"]
            if any(p in reply.lower() for p in gate_phrases):
                issues.append("ID gate fired unexpectedly on a non-personal query")
        if "expect_verified" in hints and hints["expect_verified"] and not ver:
            issues.append("Expected customer_verified=True but got False")
        if "expect_escalated" in hints and hints["expect_escalated"] and not esc:
            issues.append("Expected escalated=True but got False")
        if "expect_no_escalation" in hints and hints["expect_no_escalation"] and esc:
            issues.append("Escalated unexpectedly — should stay calm")
        if "expect_in_reply" in hints:
            for kw in hints["expect_in_reply"]:
                if kw.lower() not in reply.lower():
                    issues.append(f"Expected '{kw}' in reply but not found")
        if "expect_not_in_reply" in hints:
            for kw in hints["expect_not_in_reply"]:
                if kw.lower() in reply.lower():
                    issues.append(f"Found unwanted '{kw}' in reply")
        stall_phrases = ["let me check", "let me look", "allow me a moment",
                         "i'll need to gather", "i need to verify"]
        if any(p in reply.lower() for p in stall_phrases) and not tools:
            issues.append("LLM stall — said will check but called no tool")
        if len(reply.strip()) < 20:
            issues.append(f"Very short reply: '{reply.strip()}'")
        if reply.lower().count("sorry") >= 3:
            issues.append("Over-apologising (sorry × 3+)")
        if prev_verified and any(p in reply.lower() for p in
                                 ["verify your identity", "email address on your account"]):
            issues.append("Re-asked for identity after already verified")

        if issues:
            for iss in issues:
                print(f"\n  ⚠  {iss}")
                scenario_issues.append(f"T{i}: {iss}")
                issues_log.append((name, i, iss))

        prev_verified = prev_verified or ver

    print(f"\n  {'✓  No issues detected' if not scenario_issues else f'✗  {len(scenario_issues)} issue(s)'}")
    return s


# ════════════════════════════════════════════════════════════════════
# 1. Wrong item received — exchange attempt then refund
# ════════════════════════════════════════════════════════════════════
run("1. Wrong item received: exchange attempt → refund",
    note="Customer got the wrong product; wants exchange first, settles on refund",
    turns=[
        ("Hi, I have a problem with a recent order",
         {}),
        ("My email is demo@atlas.local and my order is ORD-88210",
         {"expect_verified": True}),
        ("I ordered Blue Wireless Headphones but received a completely different product",
         {"expect_no_escalation": True}),
        ("What is the current status of ORD-88210?",
         {"expect_tool": "lookup_order"}),
        ("Can I get an exchange instead of a refund?",
         {"expect_no_id_gate": True}),
        ("What is your exchange policy?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("Do I need to pay return shipping for a wrong item?",
         {"expect_no_id_gate": True}),
        ("How long does the return process take?",
         {"expect_no_id_gate": True}),
        ("OK forget the exchange, just process a refund for ORD-88210",
         {"expect_tool": "process_refund"}),
        ("Has the refund been initiated?",
         {"expect_in_reply": ["refund"]}),
        ("How many days until I see it on my statement?",
         {"expect_no_id_gate": True}),
        ("Thanks, I appreciate your help",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 2. Loyalty membership deep-dive — Alice Johnson
# ════════════════════════════════════════════════════════════════════
run("2. Loyalty deep-dive: tier benefits, order count, upgrade path",
    note="Alice explores her account thoroughly — no order actions, just account/product questions",
    turns=[
        ("Hi! I'm curious about my membership benefits",
         {}),
        ("My email is alice.johnson@demo.atlas",
         {"expect_verified": True}),
        ("What tier am I currently on?",
         {"expect_tool": "get_account_info"}),
        ("What benefits does my tier include?",
         {"expect_no_id_gate": True}),
        ("How many total orders have I placed?",
         {"expect_tool": "get_account_info"}),
        ("Is there a tier above mine? What does it offer?",
         {"expect_no_id_gate": True}),
        ("How do I qualify for the next tier up?",
         {"expect_no_id_gate": True}),
        ("Do higher tiers get free expedited shipping?",
         {"expect_no_id_gate": True}),
        ("What categories of products do you carry?",
         {"expect_no_id_gate": True}),
        ("Can you recommend a good laptop bag for me?",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Does my tier give me any discount on that?",
         {"expect_no_id_gate": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 3. Holiday delivery deadline panic
# ════════════════════════════════════════════════════════════════════
run("3. Holiday delivery panic: expedite → cancel attempt → return fallback",
    note="Customer needs order before a deadline; shipped so can't cancel; learns return option",
    turns=[
        ("Hi I need urgent help, I need my order before Christmas",
         {}),
        ("demo@atlas.local, order ORD-88210",
         {"expect_verified": True, "expect_tool": "lookup_order"}),
        ("When is it estimated to arrive?",
         {"expect_in_reply": ["2026-05-08"]}),
        ("That's too late — can I upgrade to overnight shipping?",
         {"expect_no_id_gate": True}),
        ("What shipping options do you offer normally?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("Since it already shipped, can I just cancel it?",
         {"expect_tool": "cancel_order", "expect_in_reply": ["shipped"]}),
        ("So I can't cancel because it already shipped?",
         {"expect_in_reply": ["return"]}),
        ("If it arrives after my deadline can I return it unopened?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("How long is the return window?",
         {"expect_no_id_gate": True}),
        ("Does the return window start from the order date or delivery date?",
         {"expect_no_id_gate": True}),
        ("OK fine, I'll wait and return it if needed. Thanks",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 4. Billing dispute — perceived double charge → escalation → refund
# ════════════════════════════════════════════════════════════════════
run("4. Billing dispute: suspected double charge → escalation → refund",
    note="Customer believes they were charged twice; builds frustration; escalates; resolves with refund",
    turns=[
        ("I think I was charged twice for my order",
         {}),
        ("My email is demo@atlas.local",
         {"expect_verified": True}),
        ("I see two charges of $89.99 on my bank statement for order ORD-88210",
         {"expect_tool": "lookup_order"}),
        ("My order total was $89.99 so why was I charged $179.98?",
         {"expect_no_escalation": True}),
        ("This is completely unacceptable — I want my money back immediately",
         {"expect_escalated": True}),
        ("I want to speak to a supervisor right now",
         {"expect_escalated": True}),
        ("Fine, can you at least process a refund for ORD-88210?",
         {"expect_tool": "process_refund"}),
        ("Has the refund been confirmed?",
         {"expect_in_reply": ["refund"]}),
        ("How long will it take to appear on my statement?",
         {"expect_no_id_gate": True}),
        ("Will the refund go back to the original payment method?",
         {"expect_no_id_gate": True}),
        ("And how do I prevent being double charged in future?",
         {"expect_no_id_gate": True}),
        ("OK, thanks for sorting that out",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 5. Product defect — warranty claim → refund
# ════════════════════════════════════════════════════════════════════
run("5. Product defect: warranty claim → refund request",
    note="Headphones stopped working after 3 weeks; warranty inquiry then refund",
    turns=[
        ("Hello, the product I bought stopped working after just 3 weeks",
         {}),
        ("My email is demo@atlas.local and my order is ORD-88210",
         {"expect_verified": True, "expect_tool": "lookup_order"}),
        ("The Blue Wireless Headphones — one side has no sound at all",
         {"expect_no_escalation": True}),
        ("Is this covered under your warranty?",
         {"expect_tool": "search_policy_knowledge"}),
        ("What is the warranty period for electronics?",
         {"expect_no_id_gate": True}),
        ("Do I need to send the item back for a warranty claim?",
         {"expect_no_id_gate": True}),
        ("Who covers the return shipping cost for a defective item?",
         {"expect_no_id_gate": True}),
        ("Would I get the same product or a different one as replacement?",
         {"expect_no_id_gate": True}),
        ("Actually I'd rather just get a refund than a replacement",
         {}),
        ("Please process a refund for order ORD-88210",
         {"expect_tool": "process_refund"}),
        ("Great. Can you recommend a more durable alternative headphone?",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("What's the warranty on that one?",
         {"expect_no_id_gate": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 6. Discount and promo hunt — no identity needed throughout
# ════════════════════════════════════════════════════════════════════
run("6. Discount and promo hunt: all general inquiry, no ID needed",
    note="Pure policy/product questions — ID gate must never fire",
    turns=[
        ("Do you have any discount codes or promotions right now?",
         {"expect_no_id_gate": True, "expect_no_escalation": True}),
        ("Do you offer student discounts?",
         {"expect_no_id_gate": True}),
        ("What about a first-time buyer discount?",
         {"expect_no_id_gate": True}),
        ("Do you have bundle deals on electronics?",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("I'm looking for wireless earbuds and a phone stand together",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Do you have any loyalty rewards?",
         {"expect_no_id_gate": True}),
        ("How do I earn points or rewards?",
         {"expect_no_id_gate": True}),
        ("Are there seasonal sales coming up?",
         {"expect_no_id_gate": True}),
        ("What is the cheapest wireless earbud you carry?",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Do you price match if I find it cheaper elsewhere?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("What's your lowest price guarantee policy?",
         {"expect_no_id_gate": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 7. Full emotional arc — calm → frustrated → escalated → resolved
# ════════════════════════════════════════════════════════════════════
run("7. Full emotional arc: calm start → frustration peak → de-escalation → resolution",
    note="Tracks sentiment arc across 12 turns; escalation must fire at peak, drop after calm",
    turns=[
        ("Hi, I'm just checking on an order I placed",
         {}),
        ("My email is demo@atlas.local, order ORD-88210",
         {"expect_verified": True, "expect_tool": "lookup_order"}),
        ("OK it says shipped. The tracking hasn't moved in 9 days though",
         {"expect_no_escalation": True}),
        ("I've emailed before about this and got no response. This is frustrating",
         {"expect_no_escalation": True}),
        ("This is absolutely ridiculous. I've been waiting 3 weeks",
         {"expect_escalated": True}),
        ("I want a full refund AND I want to speak to a manager",
         {"expect_escalated": True}),
        ("Fine. Just process my refund for ORD-88210",
         {"expect_tool": "process_refund"}),
        ("OK thank you for processing that",
         {}),
        ("I appreciate it. I was just really frustrated",
         {"expect_no_escalation": True}),
        ("What's a good replacement product you'd recommend?",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Thanks. One last thing — what's your return policy if I don't like it?",
         {"expect_no_id_gate": True}),
        ("Great, you've been helpful. Thank you",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 8. Account security concern — suspicious activity review
# ════════════════════════════════════════════════════════════════════
run("8. Account security concern: unauthorized access worry → order review",
    note="Customer suspects account compromise; reviews orders; no data leakage",
    turns=[
        ("I think someone may have accessed my account without my permission",
         {}),
        ("My email is demo@atlas.local",
         {"expect_verified": True}),
        ("I saw some activity I don't recognize — can you check my recent orders?",
         {"expect_tool": "get_account_info"}),
        ("What is my current order count?",
         {"expect_tool": "get_account_info"}),
        ("Can you look up order ORD-88210 — did I place that?",
         {"expect_tool": "lookup_order"}),
        ("OK that one is mine. What items are in it?",
         {"expect_in_reply": ["headphone"]}),
        ("How do I secure my account going forward?",
         {"expect_no_id_gate": True}),
        ("Can you see my payment method on file?",
         {"expect_not_in_reply": ["credit card number", "card number", "4111", "visa"]}),
        ("What personal data do you store on my account?",
         {"expect_not_in_reply": ["password", "ssn", "social security"]}),
        ("How do I delete my account if I want to?",
         {"expect_no_id_gate": True}),
        ("OK thanks, I think I'm OK. I'll change my password as a precaution",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 9. Multi-category product recommendation chain — no ID needed
# ════════════════════════════════════════════════════════════════════
run("9. Multi-category product hunt: earbuds → laptop stand → phone case → camera",
    note="Pure product browsing across categories; ID gate must never fire",
    turns=[
        ("Hi, I'm shopping for a few things today",
         {"expect_no_id_gate": True}),
        ("First I need some wireless earbuds under $50",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Do any of those have active noise cancellation?",
         {"expect_no_id_gate": True,
          "expect_not_in_reply": ["cancel your order", "cancellation"]}),
        ("OK great, I also need a laptop stand for a 15 inch laptop",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Does it need to be adjustable in height?",
         {"expect_no_id_gate": True}),
        ("Yes, height adjustable please, and foldable for travel",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("What is the weight limit on that stand?",
         {"expect_no_id_gate": True}),
        ("I also want a phone case — what brands do you carry?",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Do you have one for an iPhone 15?",
         {"expect_no_id_gate": True}),
        ("What is the return policy if I order all three and one doesn't fit?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("Do you offer free shipping if I order multiple items?",
         {"expect_no_id_gate": True}),
        ("Perfect, thanks for all the help",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 10. Slow credential reveal — vague opener, drip-feeds info
# ════════════════════════════════════════════════════════════════════
run("10. Slow credential reveal: vague start → drip-feeds info → verified → deep questions",
    note="Customer is slow to provide details; tests identity patience and context retention",
    turns=[
        ("hi",
         {}),
        ("I have a question about something I ordered",
         {}),
        ("It was a pair of headphones",
         {}),
        ("I ordered them maybe a week ago",
         {}),
        ("My email? It's demo@atlas.local",
         {"expect_verified": True}),
        ("The order number I think is ORD-88210",
         {"expect_tool": "lookup_order"}),
        ("Yes that's it — the Blue Wireless Headphones",
         {"expect_in_reply": ["ORD-88210"]}),
        ("When is it arriving exactly?",
         {"expect_in_reply": ["2026-05-08"]}),
        ("What carrier is delivering it?",
         {"expect_in_reply": ["UPS"]}),
        ("Can I redirect it to a different address?",
         {"expect_no_id_gate": True}),
        ("What if nobody is home when they try to deliver?",
         {"expect_no_id_gate": True}),
        ("OK thanks, that's all I needed",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 11. Refund follow-up — customer returns to check on a prior refund
# ════════════════════════════════════════════════════════════════════
run("11. Refund follow-up: customer worried refund hasn't landed yet",
    note="Customer had a refund processed; now asking about timeline and status",
    turns=[
        ("Hi, I had a refund processed recently and I'm wondering where it is",
         {}),
        ("My email is demo@atlas.local",
         {"expect_verified": True}),
        ("The refund was for order ORD-88210",
         {"expect_tool": "lookup_order"}),
        ("I was told the refund would take 3-5 business days",
         {"expect_no_escalation": True}),
        ("It's been 6 days and nothing has appeared on my bank statement",
         {"expect_no_escalation": True}),
        ("Can you check the refund status?",
         {}),
        ("What does pending_manual mean?",
         {"expect_no_id_gate": True}),
        ("How much longer will the manual review take?",
         {"expect_no_id_gate": True}),
        ("This is getting frustrating — can I escalate?",
         {"expect_escalated": True}),
        ("Fine, what is the maximum time a refund can take?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("If it doesn't arrive by next week I'm disputing with my bank",
         {"expect_no_escalation": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 12. Return window edge case — testing policy limits
# ════════════════════════════════════════════════════════════════════
run("12. Return window edge case: policy boundary questions",
    note="Customer pushes on return window details; all policy questions, no ID gate",
    turns=[
        ("What is your standard return window?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("Does the clock start from purchase date or delivery date?",
         {"expect_no_id_gate": True}),
        ("What if I ordered something as a gift and the recipient wants to return it?",
         {"expect_no_id_gate": True}),
        ("Does the gift recipient need the original receipt?",
         {"expect_no_id_gate": True}),
        ("What about items that have been opened and lightly used?",
         {"expect_no_id_gate": True}),
        ("Are electronics returnable even after being opened?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("Is there a restocking fee for returned electronics?",
         {"expect_no_id_gate": True}),
        ("What if the item is damaged during return shipping?",
         {"expect_no_id_gate": True}),
        ("Can I return an item that was on sale?",
         {"expect_no_id_gate": True}),
        ("What items are completely non-returnable?",
         {"expect_no_id_gate": True}),
        ("OK one last thing — do you offer store credit instead of a cash refund?",
         {"expect_no_id_gate": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 13. Unverified pushy customer — tries to skip ID, stays polite but firm
# ════════════════════════════════════════════════════════════════════
run("13. Persistent unverified customer: tries multiple ways to skip ID gate",
    note="Customer refuses to provide email several times before finally complying",
    turns=[
        ("I want to check on my order",
         {}),
        ("I don't want to give my email, can you just look it up?",
         {}),
        ("My name is Demo Customer, can you find me by name?",
         {}),
        ("Fine, can I at least know your return policy while I think about it?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("How long do returns take once initiated?",
         {"expect_no_id_gate": True}),
        ("OK fine, my email is demo@atlas.local",
         {"expect_verified": True}),
        ("My order number is ORD-88210",
         {"expect_tool": "lookup_order"}),
        ("What is the exact status?",
         {"expect_in_reply": ["Shipped"]}),
        ("What is the tracking number?",
         {"expect_in_reply": ["1Z999AA10123456784"]}),
        ("Can I get a refund for it?",
         {"expect_tool": "process_refund"}),
        ("Has it been confirmed?",
         {"expect_in_reply": ["refund"]}),
    ])

# ════════════════════════════════════════════════════════════════════
# 14. Post-purchase anxiety — buyer's remorse and reassurance
# ════════════════════════════════════════════════════════════════════
run("14. Buyer's remorse: second-guessing purchase, needs reassurance",
    note="Customer regrets order, asks about cancel/return, then re-commits to keeping it",
    turns=[
        ("Hi, I think I made a mistake ordering something",
         {}),
        ("I just placed an order and I'm not sure I want it anymore",
         {}),
        ("My email is demo@atlas.local and the order is ORD-88210",
         {"expect_verified": True, "expect_tool": "lookup_order"}),
        ("Can I still cancel it?",
         {"expect_tool": "cancel_order"}),
        ("Oh it already shipped? What are my options then?",
         {"expect_in_reply": ["return"]}),
        ("What is the return process if I decide I don't want it?",
         {"expect_tool": "search_policy_knowledge"}),
        ("Will I get a full refund or is there a restocking fee?",
         {"expect_no_id_gate": True}),
        ("What were the product details again for ORD-88210?",
         {"expect_tool": "lookup_order", "expect_in_reply": ["headphone"]}),
        ("Actually the Blue Wireless Headphones sound useful, maybe I'll keep them",
         {"expect_no_escalation": True}),
        ("Can you tell me more about their features?",
         {"expect_tool": "search_product_knowledge"}),
        ("OK I'll keep the order. Thanks for your patience",
         {"expect_no_escalation": True, "expect_no_id_gate": True}),
    ])

# ════════════════════════════════════════════════════════════════════
# 15. Proactive support: compliment → deep dive → new recommendation
# ════════════════════════════════════════════════════════════════════
run("15. Proactive support: happy verified customer explores full suite of services",
    note="Customer is satisfied, verifies, checks account, gets product rec, asks about referrals",
    turns=[
        ("Hi! I love shopping here, you guys are great",
         {"expect_no_escalation": True}),
        ("I want to check some details on my account",
         {}),
        ("My email is alice.johnson@demo.atlas",
         {"expect_verified": True}),
        ("What tier am I on and what benefits do I get?",
         {"expect_tool": "get_account_info"}),
        ("How many orders have I placed in total?",
         {"expect_tool": "get_account_info"}),
        ("I'm looking for a good Bluetooth speaker for a home office",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("Something under $40 with good bass and long battery",
         {"expect_no_id_gate": True, "expect_tool": "search_product_knowledge"}),
        ("What is the return policy if the sound quality isn't what I expected?",
         {"expect_no_id_gate": True, "expect_tool": "search_policy_knowledge"}),
        ("Do you have a referral program?",
         {"expect_no_id_gate": True}),
        ("Do you offer gift wrapping?",
         {"expect_no_id_gate": True}),
        ("What's the best way to stay updated on new products and sales?",
         {"expect_no_id_gate": True}),
        ("Alright, thanks so much — keep up the great work!",
         {"expect_no_escalation": True}),
    ])


# ════════════════════════════════════════════════════════════════════
# MASTER ISSUES SUMMARY
# ════════════════════════════════════════════════════════════════════
print(f"\n\n{'#'*80}")
print("  ISSUES SUMMARY ACROSS ALL 15 NEW SCENARIOS")
print(f"{'#'*80}\n")

if not issues_log:
    print("  No issues detected across all scenarios.")
else:
    by_scenario = {}
    for (sc, turn, iss) in issues_log:
        by_scenario.setdefault(sc, []).append((turn, iss))
    for sc, items in by_scenario.items():
        print(f"  ► {sc}")
        for turn, iss in items:
            print(f"       T{turn}: {iss}")
        print()

print(f"  Total issues: {len(issues_log)} across {len(by_scenario) if issues_log else 0} scenarios")
