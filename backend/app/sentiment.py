from __future__ import annotations

import re
from typing import Iterable

SENTIMENT_RULES: dict[str, list[str]] = {
    # ── High-intensity negative (escalates immediately) ──────────────────────
    "frustrated": [
        # Anger
        "angry", "furious", "livid", "enraged", "outraged", "irate", "mad",
        "pissed", "pissed off", "so mad", "very angry", "really angry",
        "extremely angry", "seething", "fuming",
        # Frustration
        "frustrated", "so frustrated", "very frustrated", "extremely frustrated",
        "beyond frustrated", "deeply frustrated", "totally frustrated",
        "fed up", "had enough", "done with this", "sick of this", "sick and tired",
        "can't take this", "this is too much", "enough is enough",
        # Annoyance
        "annoyed", "so annoyed", "very annoyed", "really annoyed",
        "irritated", "aggravated", "infuriated",
        # Disgust / contempt
        "disgusting", "disgusted", "pathetic", "shameful", "shameless",
        "disgrace", "disgraceful", "embarrassing", "embarrassed",
        "absurd", "outrageous", "unacceptable", "unbelievable",
        "ridiculous", "this is a joke", "what a joke", "laughable",
        # Strong negative descriptors
        "terrible", "awful", "horrible", "horrendous", "dreadful",
        "atrocious", "appalling", "deplorable", "abysmal",
        "worst", "worst ever", "worst experience", "absolute worst",
        "useless", "worthless", "pointless", "hopeless",
        "incompetent", "clueless",
        # Trust / integrity
        "scam", "fraud", "rip off", "ripoff", "con", "cheated", "lied",
        "deceived", "misleading", "false advertising", "wasted my money",
        "wasted my time", "waste of money", "waste of time",
        # Finality
        "never again", "never buying", "never ordering", "cancel everything",
        "closing my account", "deleting my account", "done with you",
        "last time", "last order", "switching to",
        # Escalation language
        "speak to a manager", "talk to a manager", "get me a supervisor",
        "this is not okay", "not acceptable", "completely unacceptable",
        "want to complain", "filing a complaint", "taking legal action",
        "reporting you", "leaving a review", "1 star",
        # Raw expressions
        "wtf", "what the hell", "what the heck", "what is going on",
        "are you kidding", "are you serious", "seriously",
        "i cannot believe", "i can't believe", "unreal",
    ],

    # ── Moderate negative (unhappy but not explosive) ─────────────────────────
    "negative": [
        # Problem words
        "problem", "issue", "issues", "trouble", "concern", "complaint",
        "error", "mistake", "fault", "defect", "flaw",
        # Product / order state
        "broken", "damaged", "defective", "faulty", "not working",
        "doesn't work", "stopped working", "won't work", "failed",
        "missing", "lost", "wrong", "incorrect", "incomplete",
        # Delivery
        "late", "delayed", "overdue", "still waiting", "not arrived",
        "never received", "still haven't received", "hasn't arrived",
        "never arrived", "not delivered", "not here yet",
        # Quality
        "bad", "poor", "low quality", "cheap", "flimsy", "falling apart",
        "not as described", "not what i expected", "not what i ordered",
        "different from", "not the same",
        # Emotional disappointment
        "disappointed", "disappointing", "disappointment",
        "unhappy", "not happy", "very unhappy", "really unhappy",
        "upset", "quite upset", "pretty upset", "really upset",
        "sad", "really sad", "feel sad", "feeling sad",
        "displeased", "dissatisfied", "not satisfied", "unsatisfied",
        "let down", "feel let down", "feeling let down",
        "heartbroken", "gutted", "devastated",
        "not impressed", "unimpressed", "underwhelmed",
        "regret", "regretful", "wish i hadn't",
        "feel cheated", "feel ignored", "feel neglected",
        "not good", "not great", "not okay", "not acceptable",
        # Service
        "slow", "too slow", "taking forever", "taking too long",
        "no response", "no reply", "haven't heard back",
        "ignored", "no one helped", "no help",
        "rude", "disrespectful", "unprofessional",
        # Unable
        "unable", "can't", "cannot", "couldn't", "unable to",
        "still not", "still no", "still waiting",
    ],

    # ── Positive ──────────────────────────────────────────────────────────────
    "positive": [
        "thank", "thanks", "thank you", "many thanks", "much appreciated",
        "great", "excellent", "amazing", "wonderful", "fantastic",
        "awesome", "brilliant", "superb", "outstanding", "exceptional",
        "perfect", "flawless", "seamless", "smooth",
        "love", "loved", "loving it", "really love",
        "happy", "very happy", "really happy", "so happy",
        "pleased", "very pleased", "delighted",
        "satisfied", "very satisfied", "completely satisfied",
        "appreciate", "appreciated", "grateful", "thankful",
        "helpful", "very helpful", "so helpful", "super helpful",
        "impressed", "very impressed", "pleasantly surprised",
        "good job", "well done", "great job", "keep it up",
        "easy", "simple", "quick", "fast", "efficient",
        "resolved", "sorted", "fixed", "solved",
    ],
}

INTENT_RULES: dict[str, list[str]] = {
    "track_order": ["where is my order", "track", "tracking", "order status", "where's my", "shipped"],
    # Use phrases/boundaries to avoid "noise cancelling" → cancel_order
    "cancel_order": ["cancel my order", "cancel the order", "cancel order", "i want to cancel",
                     "cancellation", "cancel it", "stop my order", "don't want it anymore",
                     "no longer want"],
    "return_item": ["return", "send back", "returning"],
    "refund_request": ["refund", "money back", "charge back", "reimburse"],
    "payment_issue": ["payment", "charged", "billing", "invoice", "credit card", "double charge"],
    "account_access": ["login", "log in", "password", "locked out", "sign in"],
    "delivery_problem": ["delivery", "delivered", "not delivered", "package", "arrived damaged", "never arrived"],
    "product_inquiry": ["does it", "specifications", "compatible", "features", "tell me about", "recommend"],
    "product_defect": ["broken", "defective", "defect", "faulty", "stopped working"],
    "wrong_item": ["wrong item", "wrong product", "received wrong", "incorrect item"],
    "missing_item": ["missing", "didn't receive", "not in box", "wasn't included"],
    "complaint": ["complaint", "complain", "terrible service", "worst service"],
    "compliment": ["thank you", "great service", "excellent service"],
    "discount_inquiry": ["discount", "coupon", "promo", "promotion", "deal", "offer", "voucher"],
    "check_stock": ["in stock", "available", "availability", "do you have"],
    "escalate_to_human": [
        "speak to human", "talk to agent", "real person", "supervisor", "manager", "human agent",
        "speak with someone", "talk to someone", "speak to someone", "talk to a person",
        "speak to a person", "speak with a person", "speak with a human", "talk to a human",
        "connect me to", "transfer me", "live agent", "live person", "live support",
        "want to speak", "want to talk", "like to speak", "like to talk",
        "need to speak with", "need to talk to",
        "escalate", "can i escalate", "i want to escalate", "need to escalate",
        "escalate this", "escalate my", "escalate me", "escalate now",
        "raise a complaint", "file a complaint", "lodge a complaint",
    ],
    "shipping_options": ["shipping", "how long", "delivery time", "express", "overnight", "free shipping"],
}

# ── Tricky / edge-case frustration patterns ──────────────────────────────────
# These are patterns a normal keyword scan will MISS.
# Ordered from most specific to most general.
_TRICKY_FRUSTRATED_RE = re.compile(
    # Sarcasm — must be before keyword scan so "great/thanks" don't fire positive
    r'oh\s+great|oh\s+perfect|oh\s+wonderful|oh\s+fantastic|oh\s+sure|oh\s+really'
    r'|just\s+perfect|just\s+wonderful|just\s+great|yeah\s+right'
    r'|thanks\s+for\s+nothing|some\s+help\s+you\s+are|great\s+job\s+guys'
    r'|oh\s+wow\s+amazing|how\s+convenient|how\s+(un)?helpful|nice\s+one\b|good\s+one\b'
    # Internet slang
    r'|\bsmh\b|\bsmfh\b|\bfml\b|\bwtf\b|\bwth\b|\bbruh\b|\bngl\b'
    r'|ugh+\b|argh+\b|grr+\b|\boof\b|\byikes\b|big\s+yikes'
    r'|\bnot\s+cool\b|\bnot\s+okay\b|\bthis\s+aint\s+it\b'
    r'|\btrash\b|\bgarbage\b|\brubbish\b|absolute\s+rubbish'
    # Rhetorical frustration questions
    r'|seriously\s*[?!]|are\s+you\s+kidding|are\s+you\s+serious'
    r'|is\s+this\s+a\s+joke|what\s+is\s+going\s+on|what\s+is\s+happening'
    r'|how\s+is\s+this\s+(even\s+)?possible|why\s+is\s+this\s+so\s+hard'
    r'|can\s+you\s+not|come\s+on\s*[!?]|what\s+the\s+heck|what\s+on\s+earth'
    # Giving up / defeated
    r'|forget\s+it\b|i\s+give\s+up|whats\s+the\s+point|what\'s\s+the\s+point'
    r'|why\s+bother|doesn\'?t\s+matter\s+anymore|it\s+is\s+what\s+it\s+is'
    r'|\bi\s*\'?m\s+done\b|done\s+with\s+this|so\s+done|completely\s+done'
    r'|i\s+am\s+done\b|forget\s+this'
    # Nth time / repeat frustration
    r'|\d+\s*(st|nd|rd|th)\s+time\b|third\s+time|fourth\s+time|again\s+and\s+again'
    r'|keep\s+(asking|trying|waiting|calling|emailing)'
    r'|asked\s+(multiple|several|many)\s+times|how\s+many\s+times'
    r'|every\s+single\s+time'
    # Desperate / pleading
    r'|please\s+just|just\s+please|i\'?m\s+begging|i\s+beg\s+you'
    r'|after\s+all\s+this|at\s+this\s+point\b',
    re.IGNORECASE,
)

_TRICKY_NEGATIVE_RE = re.compile(
    # Negated positives: "not happy", "not satisfied", "not what i expected"
    r'not\s+(at\s+all\s+)?(happy|satisfied|pleased|impressed|good|great|okay|ok'
    r'|helpful|working|right|fair|acceptable|what\s+i\s+expected|what\s+i\s+wanted'
    r'|what\s+i\s+ordered|worth\s+(it|the\s+money)|as\s+described)'
    # "un" spaced words: "un happy", "un satisfied"
    r'|un\s+(happy|satisfied|pleased|helpful|acceptable|fortunate|fair|comfortable)'
    # "dis" spaced words: "dis appointed", "dis pleased"
    r'|dis\s+(appointed|pleased|satisfied|respectful|honest)'
    # Minimised / polite frustration
    r'|\b(a\s+bit|kind\s+of|sort\s+of|slightly|rather|quite|pretty|somewhat)\s+'
    r'(upset|annoyed|frustrated|disappointed|unhappy|bothered|concerned|worried|angry)'
    # Getting worse
    r'|worse\s+than\b|getting\s+worse|even\s+worse|never\s+been\s+(this|so)\s+bad'
    r'|worse\s+than\s+ever|not\s+what\s+i\s+paid\s+for|not\s+worth\s+(it|the\s+money)'
    # "Still" / no response patterns
    r'|still\s+(no\b|nothing\b|waiting|broken|wrong|missing|not\b|haven\'?t)'
    r'|yet\s+to\s+(receive|get|hear)\b'
    r'|\bno\s+update\b|\bno\s+response\b|\bno\s+reply\b'
    r'|still\s+no\s+update|still\s+waiting\s+for',
    re.IGNORECASE,
)

# Catches ALL CAPS messages (high frustration signal) — min 4 uppercase words
_ALL_CAPS_RE = re.compile(r'\b[A-Z]{3,}\b.*\b[A-Z]{3,}\b.*\b[A-Z]{3,}\b')

# Catches repeated chars used for emphasis: "sooooo", "noooo", "ughhh", "whyyyy"
_REPEATED_CHARS_RE = re.compile(r'([a-z])\1{2,}', re.IGNORECASE)

# Catches common typos of frustration words
_TYPO_FRUSTRATED_RE = re.compile(
    r'\b(frustated|frustratd|frustraed|fustrated|frusrated|'
    r'anoyed|annoyd|anoyyed|'
    r'disapointed|dissapointed|disappointd|'
    r'dissatisfied|unsatisfied|'
    r'angery|angrey|'
    r'exhasted|exhuasted|'
    r'terrifble|aweful|horible)\b',
    re.IGNORECASE,
)

# ── Neutral product phrases (strip before matching) ───────────────────────────
# Phrases that look like they contain a keyword but are product/feature descriptions.
# Strip these from the text before sentiment/intent matching.
_NEUTRAL_PRODUCT_PHRASES = re.compile(
    r'\bnoise[- ]cancel(?:l?ing|l?ation|l?er)?\b'
    r'|\bactive\s+noise\s+cancel(?:l?ing|l?ation|l?er)?\b'
    r'|\bactive noise\b'
    r'|\bnc headphones?\b',
    re.IGNORECASE,
)

# Past-tense frustration references ("I was just really frustrated") are
# retrospective acknowledgements, not current emotion — strip them so they
# don't re-trigger escalation after the customer has calmed down.
_PAST_FRUSTRATION_RE = re.compile(
    r"\b(i was|i've been|i have been|i was just|i'm no longer)\s+"
    r"(?:just\s+|really\s+|very\s+|so\s+)*"
    r"(?:frustrated|upset|angry|annoyed|unhappy)\b",
    re.IGNORECASE,
)


def _strip_product_phrases(text: str) -> str:
    text = _NEUTRAL_PRODUCT_PHRASES.sub('', text)
    text = _PAST_FRUSTRATION_RE.sub('', text)
    return text


def _normalize(text: str) -> str:
    """Normalize tricky user input before sentiment matching."""
    # Collapse repeated chars: "sooooo" → "so", "ughhh" → "ugh", "noooo" → "no"
    text = _REPEATED_CHARS_RE.sub(r'\1\1', text)
    # Collapse "un happy" → "unhappy", "dis appointed" → "disappointed"
    text = re.sub(r'\b(un|dis|in|im|ir|non)\s+', r'\1', text, flags=re.IGNORECASE)
    return text


def _kw_match(text: str, keywords: list) -> bool:
    """Word-boundary aware keyword matching — prevents 'happy' firing inside 'unhappy'."""
    for kw in keywords:
        pattern = r'(?<!\w)' + re.escape(kw) + r'(?!\w)'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_sentiment(text: str) -> str:
    raw = _strip_product_phrases(text)
    normalized = _normalize(raw)
    t = normalized.lower()
    original = text  # keep original for ALL CAPS check

    # 1. ALL CAPS rage signal (must check on original before lowercasing)
    if _ALL_CAPS_RE.search(original):
        return "frustrated"

    # 2. Tricky frustrated patterns — check BEFORE keyword scan so sarcasm
    #    like "oh great" or "thanks for nothing" doesn't fire positive
    if _TRICKY_FRUSTRATED_RE.search(t) or _TYPO_FRUSTRATED_RE.search(t):
        return "frustrated"

    # 3. Tricky negative patterns — also before keyword scan
    #    catches "un happy", "dis appointed", "not happy", "a bit upset"
    if _TRICKY_NEGATIVE_RE.search(t):
        return "negative"

    # 4. Keyword match with word-boundary awareness (frustrated → negative → positive)
    for label in ("frustrated", "negative", "positive"):
        if _kw_match(t, SENTIMENT_RULES[label]):
            return label

    return "neutral"


def detect_intent(text: str) -> str:
    t = _strip_product_phrases(text).lower()
    for intent, kws in INTENT_RULES.items():
        if any(kw in t for kw in kws):
            return intent
    return "general_inquiry"


def cumulative_sentiment(history: Iterable[str]) -> str:
    counts = {"frustrated": 0, "negative": 0, "positive": 0, "neutral": 0}
    for s in history:
        counts[s] = counts.get(s, 0) + 1
    if counts["frustrated"] >= 1:
        return "frustrated"
    # Require 3 negative turns (not 2) before treating as frustrated —
    # prevents policy FAQ chains from triggering premature escalation.
    if counts["negative"] >= 3:
        return "frustrated"
    if counts["negative"] >= 1:
        return "negative"
    if counts["positive"] >= 2:
        return "positive"
    return "neutral"


def should_escalate(sentiment: str, cumulative: str, intent: str) -> bool:
    # Explicit escalation intent always wins regardless of sentiment.
    if intent == "escalate_to_human":
        return True
    # De-escalation guard: if the customer is now positive or offering a compliment,
    # don't keep the escalated flag raised from a prior frustrated turn.
    if sentiment == "positive" or intent == "compliment":
        return False
    # Current turn is frustrated — escalate immediately.
    if sentiment == "frustrated":
        return True
    # Session-level frustration (cumulative), but only if the current turn isn't neutral/positive.
    if cumulative == "frustrated" and sentiment not in ("positive", "neutral"):
        return True
    if intent == "complaint":
        return True
    return False
