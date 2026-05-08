# Atlas — Customer Support Agent
### DATA 298B · Team 1 · Suharsha Cheedalla

---

## What This System Is

Atlas is a full-stack AI-powered customer support agent built for an e-commerce platform. It combines a **fine-tuned Phi-4-mini language model** hosted on HuggingFace with a **Retrieval-Augmented Generation (RAG)** pipeline, deterministic tool routing, identity verification, and a customer-facing chat UI.

The system was built iteratively across two presentation milestones for SJSU DATA 298B.

---

## What Happened — Build Summary

### Phase 1 — Core Infrastructure
- FastAPI backend with PostgreSQL (orders, customers, sessions) and Qdrant vector DB
- Amazon product catalog (~350K items) ingested into Qdrant for dense retrieval
- Policy knowledge base (returns, refunds, shipping, warranties) ingested as a second Qdrant collection
- Seed data: 4 demo customers, 100+ generated orders across tiers (Gold, Silver, Platinum)
- Vanilla JS frontend with a customer-facing chat UI and an internal agent debug view
- Docker Compose stack: `api`, `postgres`, `qdrant`, `mailhog`

### Phase 2 — LLM Integration & Fine-Tuning
- Evaluated 4 models: LLaMA-3.2-1B, SmolLM2-1.7B, Qwen2.5-1.5B, **Phi-4-mini-instruct** (selected)
- Fine-tuned Phi-4-mini on a custom customer support dataset using QLoRA (4-bit) on Google Colab A100
- Deployed fine-tuned adapter to **HuggingFace Inference Endpoints** (A10G GPU)
- Built deterministic tool routing (keyword/regex) replacing unreliable LLM-generated tool calls
- Tools: `lookup_order`, `process_refund`, `cancel_order`, `get_account_info`, `search_product_knowledge`, `search_policy_knowledge`, `escalate_to_human`, `send_customer_email`

### Phase 3 — Hardening & Evaluation
- Identity verification gate: customers must provide email/order ID before accessing personal data
- Two-layer LLM safety net: stall detection regex + data-presence check → deterministic template fallback
- Frustrated customer bypass: persistent frustration skips the ID gate and routes to empathy
- Escalation routing with 20+ phrase variants (supervisor, manager, live agent, etc.)
- Fixed substring false positives: "noise cancelling" → no longer triggers cancel flow; "return window" → no longer triggers ID gate
- G-Eval evaluation framework: 50 hand-crafted test cases, Gemini 2.5 Flash as judge
- Frontend improvements: chip auto-submit, message timestamps, identity-verified chip, better error messages

### Evaluation Results (Fine-tuned Phi-4-mini + RAG, 50 test cases)
| Metric | Score |
|--------|-------|
| ROUGE-L | 0.191 |
| Task Success Rate | 72.3% |
| G-Eval avg (1–5) | 3.79 |
| Relevance | 4.24 |
| Tone & Empathy | 4.18 |
| Faithfulness | 3.78 |
| Groundedness | 3.44 |
| Completeness | 3.30 |

Best category: Escalation (4.80 G-Eval). Weakest: Cancellation (2.73).

---

## How to Run This on Your Laptop

### Prerequisites
- Docker Desktop installed and running
- Python 3.10+
- A HuggingFace account with the fine-tuned Phi-4-mini adapter deployed as an Inference Endpoint

### Step 1 — Clone & Configure

```bash
git clone https://github.com/Ch-Suharsha/teammate-rag.git
cd teammate-rag
cp .env.example .env
```

Edit `.env` and fill in:

```env
# HuggingFace fine-tuned endpoint (required for LLM responses)
HF_ENDPOINT_URL=https://your-endpoint.endpoints.huggingface.cloud
HF_TOKEN=hf_your_token_here

# Database (leave as-is for local Docker)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/atlas

# Qdrant (leave as-is for local Docker)
QDRANT_URL=http://qdrant:6333

# CORS (for local dev)
CORS_ORIGINS=http://localhost:8000,http://localhost:3000
```

### Step 2 — Download the Product Dataset

The Amazon product CSV (359MB) is too large for GitHub. Download it separately and place at:

```
data/amazon_products_final.csv
```

Or use your own catalog CSV with columns: `asin`, `title`, `category`, `price`, `stars`, `description`.

### Step 3 — Start the Stack

```bash
docker compose up --build
```

This starts:
- `api` on port 8000 (FastAPI + Uvicorn)
- `postgres` on port 5432
- `qdrant` on port 6333
- `mailhog` on port 8025 (email preview)

### Step 4 — Seed & Ingest Data

Open a second terminal and run:

```bash
# Seed the database with demo customers and orders
docker exec teammate-rag-api-1 python -m app.seed

# Ingest product catalog into Qdrant
docker exec teammate-rag-api-1 python -m app.ingest

# Ingest policy knowledge base
docker exec teammate-rag-api-1 python -m app.ingest_policies
```

### Step 5 — Open the App

- **Customer chat UI**: http://localhost:8000
- **API health**: http://localhost:8000/health
- **MailHog (email preview)**: http://localhost:8025

### Demo Credentials (for identity verification)
| Email | Name | Tier |
|-------|------|------|
| demo@atlas.local | Demo Customer | Gold |
| alice.johnson@demo.atlas | Alice Johnson | Platinum |
| bob.martinez@demo.atlas | Bob Martinez | Silver |

Sample order: **ORD-88210** (belongs to demo@atlas.local)

### Running the Evaluation

```bash
pip install rouge-score requests google-genai
cd eval
python evaluate.py --gemini-key YOUR_GEMINI_API_KEY --out results.md
```

To also evaluate the fine-tuned model without RAG (Variant B):

```bash
HF_ENDPOINT_URL=https://your-endpoint.huggingface.cloud \
HF_TOKEN=hf_your_token \
python evaluate.py --gemini-key YOUR_GEMINI_API_KEY --out results.md
```

---

## Known Issues & Limitations

### LLM Reliability
- **Phi-4-mini ignores injected context**: The fine-tuned model sometimes stalls ("Let me check that for you…") instead of using the tool results already injected into its prompt. A two-layer safety net catches this and returns a deterministic template, but this makes some responses feel robotic.
- **No streaming**: Responses are returned all at once after the full LLM call completes. For longer answers, the UI shows a typing indicator but there's a noticeable delay.
- **Context window**: Multi-turn conversations beyond ~10 turns may degrade quality as the full history is passed to the model each turn.

### Identity Verification
- **Email-only identification is weak**: Providing just an email grants full account access. There's no OTP, password, or secondary factor.
- **Single-session only**: Identity is verified per chat session. If the user opens a new tab, they need to re-verify.

### RAG / Retrieval
- **amazon_products_final.csv not in repo**: The 359MB product catalog must be downloaded and ingested manually. Without it, product recommendation tools return no results.
- **Policy KB is small**: The policy knowledge base covers common scenarios but will miss edge cases not in `data/policies.csv`.
- **No re-ranking**: Qdrant returns top-k by cosine similarity with no cross-encoder re-ranking, so occasionally off-topic products appear in recommendations.

### Cancellation Flow
- **Already-shipped orders can't be cancelled**: The system correctly identifies this but the G-Eval score for cancellation (2.73/5) shows the model doesn't always communicate the "return after delivery" path clearly.

### HuggingFace Endpoint
- **Auto-pauses after inactivity**: The HF Inference Endpoint pauses itself when idle (to save GPU costs). The first message after a pause takes 30–60 seconds while the endpoint warms up, and the request may time out. You'll need to manually resume it from the HuggingFace dashboard or handle retries in the client.
- **Cold start latency**: Even when running, first-token latency on A10G is ~3–5 seconds for a 300-token response.

### Evaluation
- **No-RAG baseline not run**: Variant B (fine-tuned Phi-4-mini without RAG) evaluation is pending because the base model endpoint isn't deployed yet. The results.md comparison table is incomplete.
- **ROUGE-L is noisy**: At 0.191, ROUGE-L is low because it measures surface overlap with a reference answer — the model often gives correct answers in different words.

### Frontend
- **No persistent login**: Users are identified per session only. Closing the browser loses the verified state.
- **No mobile responsive design**: The internal agent debug view (sidebar with tools/RAG panels) doesn't render well on small screens.
- **Session storage only**: Conversation history is stored in `localStorage`. Clearing browser data loses all history.
