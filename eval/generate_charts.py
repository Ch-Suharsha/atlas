"""
Atlas Evaluation — Chart Generator
Produces 8 publication-ready charts from eval/results.md
Run: python3 generate_charts.py
Output: eval/charts/*.png
"""

import re
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
from pathlib import Path

# ── Parse results.md ────────────────────────────────────────────────
RESULTS_MD = Path(__file__).parent / "results.md"
OUT_DIR = Path(__file__).parent / "charts"
OUT_DIR.mkdir(exist_ok=True)

def parse_results():
    with open(RESULTS_MD) as f:
        text = f.read()
    cases = []
    blocks = re.split(r'### (TC\d+) — (\w+)', text)
    i = 1
    while i < len(blocks) - 2:
        tc_id, cat, body = blocks[i], blocks[i+1], blocks[i+2]
        m  = re.search(r'\*\*G-Eval avg\*\* \| \*\*([\d.]+)\*\*', body)
        m2 = re.search(r'\| Task Success \| ([\d.]+)', body)
        m3 = re.search(r'\| ROUGE-L \| ([\d.]+)', body)
        dims = {}
        for dim in ['Relevance','Faithfulness','Completeness','Tone & Empathy','Groundedness']:
            md = re.search(rf'\| G-Eval {re.escape(dim)} \| ([\d.]+)', body)
            if md:
                dims[dim] = float(md.group(1))
        cases.append({
            'id': tc_id, 'category': cat,
            'geval':   float(m.group(1))  if m  else None,
            'task_sr': float(m2.group(1)) if m2 else None,
            'rouge':   float(m3.group(1)) if m3 else None,
            'dims': dims,
        })
        i += 3
    return cases

cases = parse_results()

# ── Palette & style ─────────────────────────────────────────────────
PALETTE = {
    'order_lookup': '#4F86C6',
    'refund':       '#E07B54',
    'cancel':       '#D4566E',
    'policy':       '#6BAF92',
    'product':      '#9B72CF',
    'account':      '#F0C244',
    'escalation':   '#5CB85C',
}
CAT_ORDER  = ['order_lookup','refund','cancel','policy','product','account','escalation']
CAT_LABELS = ['Order Lookup','Refund','Cancel','Policy','Product','Account','Escalation']
DIMS       = ['Relevance','Faithfulness','Completeness','Tone & Empathy','Groundedness']
ATLAS_BLUE = '#1A3A5C'
ACCENT     = '#4F86C6'

sns.set_theme(style='whitegrid', font='DejaVu Sans')
plt.rcParams.update({'figure.dpi': 150, 'savefig.bbox': 'tight',
                     'savefig.facecolor': 'white', 'axes.spines.top': False,
                     'axes.spines.right': False})

# ── Chart 1 — Radar: G-Eval dimensions ──────────────────────────────
def chart_radar():
    vals = [4.24, 3.78, 3.30, 4.18, 3.44]
    N    = len(DIMS)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    vals_plot = vals + vals[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_facecolor('#F7F9FC')
    fig.patch.set_facecolor('white')

    # Grid rings
    for r in [1, 2, 3, 4, 5]:
        ax.plot(angles, [r]*len(angles), color='#CCCCCC', linewidth=0.6, linestyle='--')

    ax.plot(angles, vals_plot, 'o-', linewidth=2.5, color=ACCENT, markersize=7)
    ax.fill(angles, vals_plot, alpha=0.25, color=ACCENT)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(DIMS, size=11, fontweight='bold', color=ATLAS_BLUE)
    ax.set_yticks([1,2,3,4,5])
    ax.set_yticklabels(['1','2','3','4','5'], size=8, color='#888888')
    ax.set_ylim(0, 5)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.grid(False)

    for angle, val, label in zip(angles[:-1], vals, DIMS):
        ax.annotate(f'{val:.2f}', xy=(angle, val), xytext=(angle, val + 0.35),
                    ha='center', va='center', fontsize=10, fontweight='bold', color=ATLAS_BLUE)

    ax.set_title('G-Eval Dimensions\n(Fine-tuned Phi-4-mini + RAG)', size=13,
                 fontweight='bold', color=ATLAS_BLUE, pad=20)

    plt.tight_layout()
    plt.savefig(OUT_DIR / '1_radar_dimensions.png')
    plt.close()
    print('✓ 1_radar_dimensions.png')


# ── Chart 2 — Bar: G-Eval by category ───────────────────────────────
def chart_geval_by_category():
    cat_data = {c: [] for c in CAT_ORDER}
    for case in cases:
        if case['geval'] is not None and case['category'] in cat_data:
            cat_data[case['category']].append(case['geval'])
    means  = [np.mean(cat_data[c]) for c in CAT_ORDER]
    colors = [PALETTE[c] for c in CAT_ORDER]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(CAT_LABELS, means, color=colors, width=0.6, edgecolor='white', linewidth=1.2, zorder=3)
    ax.axhline(3.79, color=ATLAS_BLUE, linewidth=1.8, linestyle='--', label='Overall avg (3.79)', zorder=4)
    ax.axhline(3.5, color='#AAAAAA', linewidth=1, linestyle=':', label='Benchmark (3.5)', zorder=4)

    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.04,
                f'{val:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=10, color=ATLAS_BLUE)

    ax.set_ylim(0, 5.5)
    ax.set_ylabel('G-Eval Score (1–5)', fontsize=11, color=ATLAS_BLUE)
    ax.set_title('G-Eval Score by Support Category', fontsize=13, fontweight='bold', color=ATLAS_BLUE, pad=12)
    ax.legend(frameon=False, fontsize=9)
    ax.tick_params(axis='x', labelsize=10)
    ax.set_facecolor('#F7F9FC')
    ax.grid(axis='y', alpha=0.4, zorder=0)

    plt.tight_layout()
    plt.savefig(OUT_DIR / '2_geval_by_category.png')
    plt.close()
    print('✓ 2_geval_by_category.png')


# ── Chart 3 — Grouped bar: Task-SR vs G-Eval/5 by category ──────────
def chart_dual_metric_by_category():
    cat_ts, cat_ge = {}, {}
    for c in CAT_ORDER:
        vals_ts = [x['task_sr'] for x in cases if x['category'] == c and x['task_sr'] is not None]
        vals_ge = [x['geval']   for x in cases if x['category'] == c and x['geval']   is not None]
        cat_ts[c] = np.mean(vals_ts) if vals_ts else 0
        cat_ge[c] = np.mean(vals_ge) / 5 if vals_ge else 0   # normalise to 0-1

    x = np.arange(len(CAT_ORDER))
    w = 0.35
    fig, ax = plt.subplots(figsize=(11, 5))
    b1 = ax.bar(x - w/2, [cat_ts[c] for c in CAT_ORDER], w, label='Task Success Rate',
                color=ACCENT, edgecolor='white', zorder=3)
    b2 = ax.bar(x + w/2, [cat_ge[c] for c in CAT_ORDER], w, label='G-Eval (normalised 0–1)',
                color='#E07B54', edgecolor='white', zorder=3)

    for bar in list(b1) + list(b2):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
                f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8, color=ATLAS_BLUE)

    ax.set_xticks(x)
    ax.set_xticklabels(CAT_LABELS, fontsize=10)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel('Score (0–1)', fontsize=11, color=ATLAS_BLUE)
    ax.set_title('Task Success Rate vs G-Eval by Category', fontsize=13, fontweight='bold', color=ATLAS_BLUE, pad=12)
    ax.legend(frameon=False, fontsize=10)
    ax.set_facecolor('#F7F9FC')
    ax.grid(axis='y', alpha=0.4, zorder=0)

    plt.tight_layout()
    plt.savefig(OUT_DIR / '3_dual_metric_by_category.png')
    plt.close()
    print('✓ 3_dual_metric_by_category.png')


# ── Chart 4 — Scatter: Task-SR vs G-Eval per case, coloured by cat ──
def chart_scatter():
    fig, ax = plt.subplots(figsize=(8, 6))
    for cat in CAT_ORDER:
        sub = [c for c in cases if c['category'] == cat and c['geval'] and c['task_sr'] is not None]
        if not sub:
            continue
        x_vals = [c['task_sr'] for c in sub]
        y_vals = [c['geval']   for c in sub]
        label  = cat.replace('_', ' ').title()
        ax.scatter(x_vals, y_vals, color=PALETTE[cat], label=label,
                   s=90, edgecolors='white', linewidth=0.8, zorder=3, alpha=0.9)

    ax.axvline(0.723, color=ATLAS_BLUE, linewidth=1.2, linestyle='--', alpha=0.5, label='Avg Task-SR')
    ax.axhline(3.79,  color='#E07B54',  linewidth=1.2, linestyle='--', alpha=0.5, label='Avg G-Eval')

    ax.set_xlabel('Task Success Rate', fontsize=11, color=ATLAS_BLUE)
    ax.set_ylabel('G-Eval Score (1–5)', fontsize=11, color=ATLAS_BLUE)
    ax.set_title('Task Success Rate vs G-Eval\n(per test case, coloured by category)',
                 fontsize=13, fontweight='bold', color=ATLAS_BLUE)
    ax.legend(frameon=False, fontsize=9, loc='lower right')
    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(0.5, 5.5)
    ax.set_facecolor('#F7F9FC')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUT_DIR / '4_scatter_task_vs_geval.png')
    plt.close()
    print('✓ 4_scatter_task_vs_geval.png')


# ── Chart 5 — Heatmap: G-Eval dimension × category ──────────────────
def chart_heatmap():
    matrix = []
    for cat in CAT_ORDER:
        row = []
        for dim in DIMS:
            vals = [c['dims'].get(dim) for c in cases if c['category'] == cat and c['dims'].get(dim) is not None]
            row.append(round(np.mean(vals), 2) if vals else 0)
        matrix.append(row)

    df = np.array(matrix)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    cmap = sns.color_palette("Blues", as_cmap=True)
    im = sns.heatmap(df, annot=True, fmt='.2f', cmap=cmap,
                     xticklabels=[d.replace(' & ', '\n& ') for d in DIMS],
                     yticklabels=CAT_LABELS,
                     vmin=1, vmax=5, linewidths=0.5, linecolor='white',
                     annot_kws={'size': 11, 'weight': 'bold', 'color': ATLAS_BLUE},
                     ax=ax)
    ax.set_title('G-Eval Score Heatmap: Dimension × Category',
                 fontsize=13, fontweight='bold', color=ATLAS_BLUE, pad=14)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10, rotation=0)
    cbar = im.collections[0].colorbar
    cbar.set_label('G-Eval Score (1–5)', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT_DIR / '5_heatmap_dim_category.png')
    plt.close()
    print('✓ 5_heatmap_dim_category.png')


# ── Chart 6 — Distribution of G-Eval scores ─────────────────────────
def chart_geval_distribution():
    scores = [c['geval'] for c in cases if c['geval'] is not None]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(scores, bins=np.arange(0.75, 5.5, 0.5), color=ACCENT, edgecolor='white',
            linewidth=1.2, zorder=3, alpha=0.9, rwidth=0.85)
    ax.axvline(np.mean(scores), color='#E07B54', linewidth=2, linestyle='--',
               label=f'Mean = {np.mean(scores):.2f}')
    ax.set_xlabel('G-Eval Score (1–5)', fontsize=11, color=ATLAS_BLUE)
    ax.set_ylabel('Number of Test Cases', fontsize=11, color=ATLAS_BLUE)
    ax.set_title('Distribution of G-Eval Scores across 50 Test Cases',
                 fontsize=13, fontweight='bold', color=ATLAS_BLUE, pad=12)
    ax.legend(frameon=False, fontsize=10)
    ax.set_facecolor('#F7F9FC')
    ax.grid(axis='y', alpha=0.4, zorder=0)
    plt.tight_layout()
    plt.savefig(OUT_DIR / '6_geval_distribution.png')
    plt.close()
    print('✓ 6_geval_distribution.png')


# ── Chart 7 — Donut: test case category distribution ────────────────
def chart_donut():
    cat_counts = {c: sum(1 for x in cases if x['category'] == c) for c in CAT_ORDER}
    sizes  = [cat_counts[c] for c in CAT_ORDER]
    colors = [PALETTE[c] for c in CAT_ORDER]

    fig, ax = plt.subplots(figsize=(6.5, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, colors=colors, autopct='%1.0f%%',
        startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2),
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')
        at.set_color('white')

    ax.text(0, 0, '50\ncases', ha='center', va='center',
            fontsize=14, fontweight='bold', color=ATLAS_BLUE)
    ax.legend(wedges, CAT_LABELS, loc='lower center', bbox_to_anchor=(0.5, -0.08),
              ncol=4, frameon=False, fontsize=9)
    ax.set_title('Test Case Distribution by Category', fontsize=13,
                 fontweight='bold', color=ATLAS_BLUE, pad=12)
    plt.tight_layout()
    plt.savefig(OUT_DIR / '7_category_distribution.png')
    plt.close()
    print('✓ 7_category_distribution.png')


# ── Chart 8 — Summary metrics dashboard ─────────────────────────────
def chart_summary_dashboard():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
    fig.patch.set_facecolor('white')

    metrics = [
        ('Task Success\nRate', 0.723, 1.0, '#4F86C6', '72.3%'),
        ('G-Eval Score\n(avg 1–5)', 3.79, 5.0, '#6BAF92', '3.79 / 5'),
        ('ROUGE-L', 0.191, 1.0, '#E07B54', '0.191'),
    ]

    for ax, (label, val, max_val, color, display) in zip(axes, metrics):
        # Background circle
        theta = np.linspace(0, 2*np.pi, 200)
        ax.plot(np.cos(theta), np.sin(theta), color='#E8EEF4', linewidth=18, solid_capstyle='round')
        # Progress arc
        frac   = val / max_val
        theta2 = np.linspace(np.pi/2, np.pi/2 - 2*np.pi*frac, 200)
        ax.plot(np.cos(theta2), np.sin(theta2), color=color, linewidth=18, solid_capstyle='round')
        # Value text
        ax.text(0, 0.1, display, ha='center', va='center',
                fontsize=16, fontweight='bold', color=ATLAS_BLUE)
        ax.text(0, -0.35, label, ha='center', va='center',
                fontsize=11, color='#555555', multialignment='center')
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_facecolor('white')

    fig.suptitle('Atlas — Overall Evaluation Metrics\n(Fine-tuned Phi-4-mini + RAG · 50 test cases)',
                 fontsize=13, fontweight='bold', color=ATLAS_BLUE, y=1.02)
    plt.tight_layout()
    plt.savefig(OUT_DIR / '8_summary_dashboard.png')
    plt.close()
    print('✓ 8_summary_dashboard.png')


# ── Run all ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'\nGenerating charts → {OUT_DIR}\n')
    chart_radar()
    chart_geval_by_category()
    chart_dual_metric_by_category()
    chart_scatter()
    chart_heatmap()
    chart_geval_distribution()
    chart_donut()
    chart_summary_dashboard()
    print(f'\nAll charts saved to {OUT_DIR}')
