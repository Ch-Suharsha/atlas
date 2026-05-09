"""
Shared test cases for fine-tuned vs fine-tuned+RAG vs base model comparison.
50 cases across 3 categories: policy (25), behavioral (15), operational (10).

Operational cases (needs_auth=True) require the live API (fine-tuned+RAG).
Policy + behavioral cases can be run against all 3 model configs.
"""

TEST_CASES = [

    # ─── POLICY QUESTIONS (25) ────────────────────────────────────────────────
    {
        "id": "POL-01",
        "category": "policy",
        "message": "What is your return policy?",
        "expected_keywords": ["return", "days"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-02",
        "category": "policy",
        "message": "How many days do I have to return an item?",
        "expected_keywords": ["30", "days"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-03",
        "category": "policy",
        "message": "I bought something as a gift for my mom. Can she return it if she doesn't like it?",
        "expected_keywords": ["return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-04",
        "category": "policy",
        "message": "How do I start a return for something I bought?",
        "expected_keywords": ["return", "order"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-05",
        "category": "policy",
        "message": "Are there any items that cannot be returned?",
        "expected_keywords": ["return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-06",
        "category": "policy",
        "message": "How long does a refund take after I send the item back?",
        "expected_keywords": ["business days", "refund"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-07",
        "category": "policy",
        "message": "I bought a Christmas gift in November. Can I return it in January?",
        "expected_keywords": ["January", "holiday", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-08",
        "category": "policy",
        "message": "I missed the return window by a couple of days. Is there any exception?",
        "expected_keywords": ["return", "days"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-09",
        "category": "policy",
        "message": "Do I have to pay for return shipping or is it free?",
        "expected_keywords": ["shipping", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-10",
        "category": "policy",
        "message": "My headphones broke after 2 months of normal use. Are they covered under warranty?",
        "expected_keywords": ["warranty"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-11",
        "category": "policy",
        "message": "How do I make a warranty claim for a defective product?",
        "expected_keywords": ["warranty", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-12",
        "category": "policy",
        "message": "Can I exchange my item for a different size instead of getting a refund?",
        "expected_keywords": ["exchange", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-13",
        "category": "policy",
        "message": "What does the A-to-z Guarantee cover and how do I use it?",
        "expected_keywords": ["A-to-z", "guarantee"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-14",
        "category": "policy",
        "message": "How long does standard shipping usually take?",
        "expected_keywords": ["shipping", "days"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-15",
        "category": "policy",
        "message": "My package was left on my doorstep and it went missing. What happens now?",
        "expected_keywords": ["lost", "refund", "replace"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-16",
        "category": "policy",
        "message": "Can I return a digital product or software download?",
        "expected_keywords": ["digital", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-17",
        "category": "policy",
        "message": "Will my refund go back to my credit card or will I get store credit?",
        "expected_keywords": ["refund", "payment", "original"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-18",
        "category": "policy",
        "message": "I bought from a third-party seller. Can I still return directly to you?",
        "expected_keywords": ["seller", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-19",
        "category": "policy",
        "message": "What is a partial refund and when would I get one instead of a full refund?",
        "expected_keywords": ["partial", "refund"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-20",
        "category": "policy",
        "message": "Is there a restocking fee if I return an item without the original box?",
        "expected_keywords": ["restocking", "return"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-21",
        "category": "policy",
        "message": "What is the return window specifically for electronics?",
        "expected_keywords": ["return", "days", "electronics"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-22",
        "category": "policy",
        "message": "If the seller does not respond to my return request, what are my options?",
        "expected_keywords": ["seller", "A-to-z", "48"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-23",
        "category": "policy",
        "message": "Can I get my refund as gift card balance instead of back to my bank?",
        "expected_keywords": ["gift card", "refund"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-24",
        "category": "policy",
        "message": "How long after approval does it take for the refund to show on my bank statement?",
        "expected_keywords": ["business days", "bank", "refund"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },
    {
        "id": "POL-25",
        "category": "policy",
        "message": "I returned an item but my refund was denied. Why would that happen?",
        "expected_keywords": ["denied", "return", "refund"],
        "policy_question": True,
        "expected_tool": "search_policy_knowledge",
        "needs_auth": False,
    },

    # ─── BEHAVIORAL / COMPLIANCE CASES (15) ──────────────────────────────────
    {
        "id": "BEH-01",
        "category": "behavioral",
        "message": "I'm very frustrated. My package has been delayed for 2 weeks and nobody is helping me.",
        "expected_keywords": ["sorry", "understand", "help"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-02",
        "category": "behavioral",
        "message": "This is the third problem I've had with your service. I want to speak to a manager.",
        "expected_keywords": ["sorry", "escalate", "agent"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-03",
        "category": "behavioral",
        "message": "I need help right now, it is urgent.",
        "expected_keywords": ["help", "assist"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-04",
        "category": "behavioral",
        "message": "Thank you so much, you've been really helpful!",
        "expected_keywords": ["welcome", "glad", "help"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-05",
        "category": "behavioral",
        "message": "I'm not happy with my purchase at all.",
        "expected_keywords": ["sorry", "help", "return", "refund"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-06",
        "category": "behavioral",
        "message": "Your website is not working and I cannot place my order.",
        "expected_keywords": ["sorry", "help"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-07",
        "category": "behavioral",
        "message": "Why is your return policy so strict? This is ridiculous.",
        "expected_keywords": ["understand", "sorry", "return"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-08",
        "category": "behavioral",
        "message": "I've been on hold for over an hour and nobody is helping me.",
        "expected_keywords": ["sorry", "apologize", "help"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-09",
        "category": "behavioral",
        "message": "This product is absolute garbage. I want my money back immediately.",
        "expected_keywords": ["sorry", "refund", "return"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-10",
        "category": "behavioral",
        "message": "Just tell me yes or no — can I return something I bought 35 days ago?",
        "expected_keywords": ["return", "days"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-11",
        "category": "behavioral",
        "message": "I don't understand your return policy at all. Can you explain it simply?",
        "expected_keywords": ["return", "days"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-12",
        "category": "behavioral",
        "message": "Is customer support available on weekends and holidays?",
        "expected_keywords": ["support", "help"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-13",
        "category": "behavioral",
        "message": "I am really stressed out about this order. Can you please just help me?",
        "expected_keywords": ["sorry", "help", "understand"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-14",
        "category": "behavioral",
        "message": "I want to return my item but I already threw away the original packaging.",
        "expected_keywords": ["return", "packaging"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },
    {
        "id": "BEH-15",
        "category": "behavioral",
        "message": "My item arrived damaged but I still want to keep it. What can you do for me?",
        "expected_keywords": ["partial", "refund", "credit", "sorry"],
        "policy_question": False,
        "expected_tool": None,
        "needs_auth": False,
    },

    # ─── OPERATIONAL CASES (10) — fine-tuned+RAG only ────────────────────────
    # These include customer email so the API verifies identity and calls tools.
    {
        "id": "OPS-01",
        "category": "operational",
        "message": "My email is demo@atlas.local. I want to check on order ORD-88210.",
        "expected_keywords": ["ORD-88210", "Shipped", "UPS"],
        "policy_question": False,
        "expected_tool": "lookup_order",
        "needs_auth": True,
    },
    {
        "id": "OPS-02",
        "category": "operational",
        "message": "demo@atlas.local — what is the tracking number for ORD-88210?",
        "expected_keywords": ["1Z999AA10123456784", "UPS"],
        "policy_question": False,
        "expected_tool": "lookup_order",
        "needs_auth": True,
    },
    {
        "id": "OPS-03",
        "category": "operational",
        "message": "I'm demo@atlas.local. Please cancel order ORD-88210.",
        "expected_keywords": ["shipped", "cancel", "return"],
        "policy_question": False,
        "expected_tool": "cancel_order",
        "needs_auth": True,
    },
    {
        "id": "OPS-04",
        "category": "operational",
        "message": "demo@atlas.local — please process a refund for ORD-88210.",
        "expected_keywords": ["Refund ID", "89.99", "pending"],
        "policy_question": False,
        "expected_tool": "process_refund",
        "needs_auth": True,
    },
    {
        "id": "OPS-05",
        "category": "operational",
        "message": "My email is demo@atlas.local. What membership tier am I on?",
        "expected_keywords": ["Gold", "Demo Customer"],
        "policy_question": False,
        "expected_tool": "get_account_info",
        "needs_auth": True,
    },
    {
        "id": "OPS-06",
        "category": "operational",
        "message": "demo@atlas.local — has my order ORD-88210 shipped yet?",
        "expected_keywords": ["Shipped", "UPS", "ORD-88210"],
        "policy_question": False,
        "expected_tool": "lookup_order",
        "needs_auth": True,
    },
    {
        "id": "OPS-07",
        "category": "operational",
        "message": "I'm demo@atlas.local. When will order ORD-88210 arrive?",
        "expected_keywords": ["2026-05-08", "delivery"],
        "policy_question": False,
        "expected_tool": "lookup_order",
        "needs_auth": True,
    },
    {
        "id": "OPS-08",
        "category": "operational",
        "message": "demo@atlas.local — what items are in my order ORD-88210?",
        "expected_keywords": ["Headphones", "Blue Wireless"],
        "policy_question": False,
        "expected_tool": "lookup_order",
        "needs_auth": True,
    },
    {
        "id": "OPS-09",
        "category": "operational",
        "message": "My email is demo@atlas.local. I received damaged headphones in ORD-88210 and want a refund.",
        "expected_keywords": ["Refund ID", "89.99", "initiated"],
        "policy_question": False,
        "expected_tool": "process_refund",
        "needs_auth": True,
    },
    {
        "id": "OPS-10",
        "category": "operational",
        "message": "demo@atlas.local, order ORD-88210. What is the exact current status?",
        "expected_keywords": ["Shipped", "ORD-88210", "UPS"],
        "policy_question": False,
        "expected_tool": "lookup_order",
        "needs_auth": True,
    },
]

# ─── Metric helpers ────────────────────────────────────────────────────────────

import re
import time


def policy_compliance(reply: str) -> dict:
    """4-dimension behavioral compliance check (from workbook)."""
    has_empathy = bool(re.search(
        r'\b(sorry|apologize|understand|frustrat|concern|glad|happy|here to help|care|appreciate)\b',
        reply, re.IGNORECASE
    ))
    has_next_step = bool(re.search(
        r"\b(I'll|I will|let me|please|here are|you can|contact|visit|initiate|follow|step|proceed)\b",
        reply, re.IGNORECASE
    ))
    adequate_length = len(reply.split()) >= 15
    bad_phrases = ["cannot help", "no idea", "i don't know", "unable to assist", "not able to help"]
    professional_tone = not any(p in reply.lower() for p in bad_phrases)
    score = (has_empathy + has_next_step + adequate_length + professional_tone) / 4
    return {
        "compliance_score": round(score, 2),
        "has_empathy": has_empathy,
        "has_next_step": has_next_step,
        "adequate_length": adequate_length,
        "professional_tone": professional_tone,
    }


def policy_specificity(reply: str, is_policy_question: bool) -> float | None:
    """Measures whether reply contains concrete policy details vs vague generalities.
    This is the primary RAG advantage metric — RAG-grounded replies score higher."""
    if not is_policy_question:
        return None
    specific_patterns = [
        r'\b\d+\s*(days?|hours?|weeks?|months?|business days?)\b',  # time windows
        r'\b\d+\s*%\b',                                               # percentages (restocking fee)
        r'\$\d+',                                                      # dollar amounts
        r'\b(30|60|90|31)\s*days?\b',                                  # common return windows
        r'\b3[\-–]5\s*business\s*days?\b',                             # standard refund timeline
        r'\b48\s*hours?\b',                                            # seller response window
        r'\b(january|november|december)\b',                            # holiday return months
        r'\bA[\-–]to[\-–]z\b',                                        # A-to-z guarantee name
        r'\bpre[\-–]paid\s*return\s*label\b',                         # specific return shipping
        r'\boriginal\s*payment\s*method\b',                           # specific refund destination
    ]
    hits = sum(1 for p in specific_patterns if re.search(p, reply, re.IGNORECASE))
    return round(min(hits / 3, 1.0), 2)  # ≥3 specific details = perfect score


def response_relevance(reply: str, expected_keywords: list) -> float:
    """% of expected keywords present in the reply."""
    if not expected_keywords:
        return 1.0
    hits = sum(1 for kw in expected_keywords if kw.lower() in reply.lower())
    return round(hits / len(expected_keywords), 2)


def hallucination_check(reply: str, message: str) -> int:
    """1 = hallucination detected, 0 = clean."""
    # Fabricated order ID not mentioned in the input
    order_in_input = set(re.findall(r'ORD-[\w]+', message, re.IGNORECASE))
    order_in_reply = set(re.findall(r'ORD-[\w]+', reply, re.IGNORECASE))
    if order_in_reply - order_in_input:
        return 1
    # Fabricated tracking number
    track_in_input = bool(re.search(r'1Z[A-Z0-9]{16}', message))
    track_in_reply = bool(re.search(r'1Z[A-Z0-9]{16}', reply))
    if track_in_reply and not track_in_input:
        return 1
    # Fabricated specific dollar amounts not in input
    amounts_input = set(re.findall(r'\$[\d,.]+', message))
    amounts_reply = set(re.findall(r'\$[\d,.]+', reply))
    if amounts_reply - amounts_input:
        return 1
    return 0


def fcr_classify(reply: str) -> str:
    """Classify resolution status: resolved / escalated / needs_followup."""
    r = reply.lower()
    if any(w in r for w in ['human agent', 'transfer', 'escalate', 'manager', 'supervisor', 'connecting you']):
        return 'escalated'
    resolution_words = ["i've", "i have", "i will", "processed", "initiated", "submitted",
                        "here are the steps", "your order", "your refund", "your account"]
    if any(w in r for w in resolution_words):
        return 'resolved'
    question_count = reply.count('?')
    if question_count > 1:
        return 'needs_followup'
    return 'resolved'


def score_response(reply: str, test_case: dict, tools_called: list = None, latency: float = None) -> dict:
    """Run all metrics on a single response and return a result dict."""
    compliance = policy_compliance(reply)
    specificity = policy_specificity(reply, test_case.get("policy_question", False))
    relevance = response_relevance(reply, test_case.get("expected_keywords", []))
    hallucination = hallucination_check(reply, test_case["message"])
    fcr = fcr_classify(reply)

    tool_correct = None
    if tools_called is not None and test_case.get("expected_tool"):
        tool_correct = test_case["expected_tool"] in (tools_called or [])

    return {
        "id": test_case["id"],
        "category": test_case["category"],
        "message": test_case["message"][:60] + "...",
        "reply_preview": reply[:120] + "..." if len(reply) > 120 else reply,
        "compliance_score": compliance["compliance_score"],
        "has_empathy": compliance["has_empathy"],
        "has_next_step": compliance["has_next_step"],
        "adequate_length": compliance["adequate_length"],
        "professional_tone": compliance["professional_tone"],
        "policy_specificity": specificity,
        "response_relevance": relevance,
        "hallucination": hallucination,
        "fcr": fcr,
        "tool_correct": tool_correct,
        "latency_s": round(latency, 2) if latency is not None else None,
    }
