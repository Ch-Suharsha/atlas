"""
Atlas System Architecture Diagram
DATA 298B · Team 1 · Suharsha Cheedalla
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Canvas ─────────────────────────────────────────────────────────────────────
FW, FH = 26, 19
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW)
ax.set_ylim(0, FH)
ax.axis('off')
BG = '#0d1117'
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# (bg, border)
PAL = {
    'client':  ('#0c1f38', '#58a6ff'),
    'api':     ('#0d1f2d', '#388bfd'),
    'proc':    ('#151528', '#7c8dff'),
    'tool':    ('#0c1f14', '#3fb950'),
    'pg':      ('#0c200e', '#3fb950'),
    'qd':      ('#180c2a', '#a371f7'),
    'hf':      ('#2c1a0c', '#d29922'),
    'mail':    ('#2c0c0c', '#f85149'),
    'ingest':  ('#161b22', '#8b949e'),
    'embed':   ('#0c1a2c', '#79c0ff'),
    'eval':    ('#1c1a0c', '#e3b341'),
}
TEXT  = '#e6edf3'
MUTED = '#8b949e'
GRID  = '#21262d'


def bg(k): return PAL[k][0]
def bd(k): return PAL[k][1]


def rbox(x, y, w, h, title, sub='', k='api', fs=9, sfs=7.5):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0.12',
        facecolor=bg(k), edgecolor=bd(k),
        linewidth=1.8, zorder=3,
    ))
    cy = y + h / 2
    if sub:
        ax.text(x + w / 2, cy + h * 0.17, title,
                ha='center', va='center', color=TEXT,
                fontsize=fs, fontweight='bold', zorder=5)
        ax.text(x + w / 2, cy - h * 0.23, sub,
                ha='center', va='center', color=MUTED,
                fontsize=sfs, zorder=5, linespacing=1.45)
    else:
        ax.text(x + w / 2, cy, title,
                ha='center', va='center', color=TEXT,
                fontsize=fs, fontweight='bold', zorder=5)


def arr(x1, y1, x2, y2, k='api', lw=1.5, label='', lfs=7.5, rad=0.0):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle='->', color=bd(k), lw=lw,
                    connectionstyle=f'arc3,rad={rad}',
                ), zorder=2)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.12, my, label, color=MUTED, fontsize=lfs, zorder=5)


def darr(x1, y1, x2, y2, k='embed', lw=1.3):
    """Dashed arrow from (x1,y1) → (x2,y2)."""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle='->', color=bd(k), lw=lw,
                    linestyle='dashed',
                ), zorder=2)


def sec(x, y, text):
    ax.text(x, y, text, color=MUTED, fontsize=8,
            fontweight='bold', style='italic', zorder=5)


# ═══════════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════════
ax.text(13, 18.55, 'Atlas  ·  Customer Support Agent',
        ha='center', color=TEXT, fontsize=19, fontweight='bold', zorder=5)
ax.text(13, 18.05, 'Full System Architecture  ·  DATA 298B  ·  Team 1',
        ha='center', color=MUTED, fontsize=11, zorder=5)
ax.plot([1, 25], [17.78, 17.78], color=GRID, lw=1.2, zorder=2)

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT   y = 16.55 – 17.45
# ═══════════════════════════════════════════════════════════════════════════════
sec(0.4, 17.52, '■  CLIENT')
rbox(7.5, 16.55, 11, 0.95,
     'Browser  /  Customer UI',
     'Vanilla JS  ·  localStorage sessions  ·  quick-start chips  ·  marked.js + DOMPurify',
     'client', fs=10.5)
arr(13, 16.55, 13, 15.9, 'client', lw=1.8, label='POST /chat')

# ═══════════════════════════════════════════════════════════════════════════════
# API GATEWAY   y = 14.85 – 15.9
# ═══════════════════════════════════════════════════════════════════════════════
sec(0.4, 16.1, '■  API GATEWAY')
rbox(3.0, 14.85, 20, 1.05,
     'FastAPI  +  Uvicorn   (port 8000)',
     '/chat    /health    /rag/search    /policy/search    /rag/stats    /webhooks/email/inbound',
     'api', fs=11)

# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSING   y = 13.25 – 14.45
# ═══════════════════════════════════════════════════════════════════════════════
sec(0.4, 14.58, '■  PROCESSING LAYER')

PY, PH = 13.25, 1.2

# Sentiment
rbox(0.4, PY, 5.2, PH,
     'Sentiment & Intent',
     'keyword / regex  ·  no LLM cost\n4 sentiments  ·  15 intent classes\nnoise-cancel phrase stripping',
     'proc', fs=9, sfs=7.3)

# Identity Gate
rbox(6.1, PY, 5.5, PH,
     'Identity Gate',
     'email + order ID  ·  4 verification cases\nfrustration bypass → empathy route\npolicy questions always exempt',
     'proc', fs=9, sfs=7.3)

# Agent
rbox(12.1, PY, 6.5, PH,
     'Agent   (agent.py)',
     'deterministic tool router\nprompt builder + context injection\n3× safety nets: stall / data-presence',
     'proc', fs=9, sfs=7.3)

# HF Endpoint (external)
rbox(20.1, PY - 0.2, 5.5, 1.55,
     'HF Inference Endpoint',
     'Fine-tuned Phi-4-mini\nQLoRA  r=16  lora_alpha=32\nA10G GPU  ·  Φ-4 chat template',
     'hf', fs=9, sfs=7.5)

# Arrows: FastAPI → processing boxes
arr(5.5,  14.85,  3.0,  14.45, 'proc', lw=1.3)
arr(10.5, 14.85,  8.85, 14.45, 'proc', lw=1.3)
arr(15.5, 14.85, 15.35, 14.45, 'proc', lw=1.3)

# Agent ↔ HF
ax.annotate('', xy=(20.1, 13.85), xytext=(18.6, 13.85),
            arrowprops=dict(arrowstyle='<->', color=bd('hf'), lw=2.0), zorder=2)
ax.text(19.1, 14.05, 'httpx · temp=0.1\nmax_tokens=300',
        color=MUTED, fontsize=7.5, ha='center', zorder=5)

# Agent → tool bus
AGENT_CX = 12.1 + 3.25  # 15.35
arr(AGENT_CX, PY, AGENT_CX, 12.55, 'tool', lw=1.5)

# ═══════════════════════════════════════════════════════════════════════════════
# TOOL LAYER   y = 10.9 – 12.2  (bus at y=12.55)
# ═══════════════════════════════════════════════════════════════════════════════
sec(0.4, 12.68, '■  TOOL LAYER   (keyword / regex dispatch  ·  tools.py)')

TW, TH, TGAP, TX0 = 2.9, 1.3, 0.14, 0.4

TOOLS = [
    ('lookup\norder',            'SQL SELECT\nownership check'),
    ('process\nrefund',          'idempotent INSERT\nSHA-1 request_key'),
    ('cancel\norder',            'status check\nProcessing only'),
    ('get_account\ninfo',        'aggregate query\ntier · orders'),
    ('search_product\nknow.',    'Qdrant cosine\nscore ≥ 0.48'),
    ('search_policy\nknow.',     'Qdrant cosine\ntop-3 results'),
    ('escalate\nto_human',       'ticket INSERT\nTKT-xxxxxx'),
    ('send_customer\nemail',     'SMTP · smtplib\nEmailLog audit'),
]

# Horizontal dispatch bus
tool_color = bd('tool')
bus_y = 12.52
bus_x0 = TX0 + TW / 2
bus_x1 = TX0 + 7 * (TW + TGAP) + TW / 2
ax.plot([bus_x0, bus_x1], [bus_y, bus_y], color=tool_color, lw=1.8, zorder=2)

for i, (name, sub) in enumerate(TOOLS):
    tx = TX0 + i * (TW + TGAP)
    tcx = tx + TW / 2
    # drop line + arrow to tool top
    ax.annotate('', xy=(tcx, TH + 10.9), xytext=(tcx, bus_y),
                arrowprops=dict(arrowstyle='->', color=tool_color, lw=1.3), zorder=2)
    rbox(tx, 10.9, TW, TH, name, sub, 'tool', fs=8.5, sfs=7.2)

# ═══════════════════════════════════════════════════════════════════════════════
# STORAGE   y = 8.5 – 10.5
# ═══════════════════════════════════════════════════════════════════════════════
sec(0.4, 10.6, '■  STORAGE  &  SERVICES')

PG_X, PG_W = 0.4,  7.5
QD_X, QD_W = 8.6,  7.0
ML_X, ML_W = 16.4, 6.2

rbox(PG_X, 8.5, PG_W, 2.0,
     'PostgreSQL 16   (port 5432)',
     'customers  ·  orders  ·  refunds\nsupport_tickets  ·  chat_sessions\nchat_messages  ·  email_log',
     'pg', fs=9.5, sfs=8.2)

rbox(QD_X, 8.5, QD_W, 2.0,
     'Qdrant  v1.12.4   (port 6333)',
     'amazon_products_2023\n(~350 K rows  ·  384-dim vectors)\nsupport_policies',
     'qd', fs=9.5, sfs=8.2)

rbox(ML_X, 8.5, ML_W, 2.0,
     'Email Service',
     'MailHog  :8025  (local dev)\nAmazon SES  (production)\nEmailLog audit  ·  SMTP STARTTLS',
     'mail', fs=9.5, sfs=8.2)

PG_CX = PG_X + PG_W / 2   # 4.15
QD_CX = QD_X + QD_W / 2   # 12.1
ML_CX = ML_X + ML_W / 2   # 19.5

# Arrows: tools → storage
for i in range(4):            # SQL → Postgres
    tcx = TX0 + i * (TW + TGAP) + TW / 2
    arr(tcx, 10.9, PG_CX, 10.5, 'pg', lw=1.2)

for i in range(4, 6):         # RAG → Qdrant
    tcx = TX0 + i * (TW + TGAP) + TW / 2
    arr(tcx, 10.9, QD_CX, 10.5, 'qd', lw=1.2)

for i in range(6, 8):         # escalate + email → Email
    tcx = TX0 + i * (TW + TGAP) + TW / 2
    arr(tcx, 10.9, ML_CX, 10.5, 'mail', lw=1.2)

# ═══════════════════════════════════════════════════════════════════════════════
# INGEST / SEED   y = 6.3 – 7.5
# ═══════════════════════════════════════════════════════════════════════════════
sec(0.4, 8.15, '■  DATA INGESTION   (one-time Docker run commands)')

rbox(0.4, 6.3, 3.8, 1.2,
     'app.seed',
     '15 customers  ·  120 orders\nupsert idempotent',
     'ingest', fs=9, sfs=7.8)

rbox(4.6, 6.3, 4.2, 1.2,
     'app.ingest',
     'amazon_products_final.csv\nbatch=256  ·  checkpointed',
     'ingest', fs=9, sfs=7.8)

rbox(9.2, 6.3, 4.2, 1.2,
     'app.ingest\n_policies',
     'policies.csv  ·  ~2 min\nUUID5 keyed  ·  idempotent',
     'ingest', fs=9, sfs=7.8)

rbox(14.2, 6.3, 5.0, 1.2,
     'Embedder  (shared)',
     'all-MiniLM-L6-v2  ·  384-dim\nlazy-load  ·  thread-safe lock',
     'embed', fs=9, sfs=7.8)

# Ingest → storage arrows
arr(2.3,  7.5, PG_CX, 8.5, 'pg',   lw=1.4)
arr(6.7,  7.5, QD_CX - 1.5, 8.5, 'qd', lw=1.4)
arr(11.3, 7.5, QD_CX + 1.0, 8.5, 'qd', lw=1.4)

# ingest → Embedder (calls embed_texts)
arr(9.2, 6.9, 14.2, 6.9, 'embed', lw=1.2, label='embed_texts()')
arr(4.6, 6.9, 14.2 - 0.05, 6.9, 'embed', lw=1.2)

# Embedder → Qdrant (runtime embed_query)
darr(16.7, 7.5, QD_CX + 2.0, 8.5, 'embed', lw=1.3)
ax.text(QD_CX + 2.5, 8.0, 'embed_query()\nruntime', color=MUTED, fontsize=7.5,
        ha='left', zorder=5)

# ═══════════════════════════════════════════════════════════════════════════════
# EVAL   y = 6.3 – 8.0
# ═══════════════════════════════════════════════════════════════════════════════
rbox(20.2, 6.3, 5.3, 1.9,
     'Evaluation  (eval/)',
     'G-Eval  ·  ROUGE-L  ·  Task-SR\n250 test cases\nGemini-2.5  ·  Claude Sonnet',
     'eval', fs=9.5, sfs=8)
ax.text(22.85, 5.95, '3.79 G-Eval  ·  72.3% Task-SR  ·  0.191 ROUGE-L',
        ha='center', color=MUTED, fontsize=8, zorder=5)
ax.text(22.85, 5.65, 'Best: Escalation 4.80',
        ha='center', color=MUTED, fontsize=8, zorder=5)

# ═══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════════════
ax.plot([0.4, 25.5], [5.35, 5.35], color=GRID, lw=1.2, zorder=2)
ax.text(0.4, 5.12, 'LEGEND:', color=MUTED, fontsize=8.5, fontweight='bold', zorder=5)

legend_items = [
    ('client', 'Client UI'),
    ('api',    'API Layer'),
    ('proc',   'Processing'),
    ('tool',   'Tools'),
    ('pg',     'PostgreSQL'),
    ('qd',     'Qdrant'),
    ('hf',     'HF Endpoint'),
    ('mail',   'Email'),
    ('embed',  'Embedder'),
    ('eval',   'Evaluation'),
]
for i, (k, label) in enumerate(legend_items):
    lx = 0.4 + i * 2.5
    ax.add_patch(FancyBboxPatch(
        (lx, 4.45), 0.42, 0.32,
        boxstyle='round,pad=0.05',
        facecolor=bg(k), edgecolor=bd(k),
        linewidth=1.5, zorder=4,
    ))
    ax.text(lx + 0.58, 4.61, label, color=MUTED, fontsize=8, va='center', zorder=5)

# ═══════════════════════════════════════════════════════════════════════════════
# DOCKER COMPOSE FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
ax.plot([0.4, 25.5], [4.1, 4.1], color=GRID, lw=1.2, zorder=2)
ax.text(13, 3.75, 'Docker Compose Stack',
        ha='center', color=MUTED, fontsize=9, fontweight='bold', zorder=5)
ax.text(13, 3.38,
        'api :8000   ·   postgres :5432   ·   qdrant :6333   ·   mailhog :8025 [--profile dev-mail]',
        ha='center', color=MUTED, fontsize=8.8, zorder=5)
ax.text(13, 3.02,
        'HuggingFace model cache volume   ·   ./data:/data:ro (read-only)   ·   ./web:/app/web',
        ha='center', color=MUTED, fontsize=8.8, zorder=5)
ax.text(13, 2.65,
        'Seed  →  docker compose run api python -m app.seed     '
        'Ingest  →  python -m app.ingest --batch-size 256     '
        'Policies  →  python -m app.ingest_policies',
        ha='center', color=MUTED, fontsize=8, zorder=5)

# bottom rule
ax.plot([0.4, 25.5], [2.35, 2.35], color=GRID, lw=1.2, zorder=2)
ax.text(13, 2.05,
        'DATA 298B  ·  Team 1  ·  Suharsha Cheedalla',
        ha='center', color='#3d4551', fontsize=9, zorder=5)

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════════
plt.savefig(
    'atlas_system_diagram.png',
    dpi=180,
    bbox_inches='tight',
    facecolor=fig.get_facecolor(),
)
print('Saved: atlas_system_diagram.png')
plt.close()
