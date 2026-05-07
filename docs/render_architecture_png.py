"""Render docs/images/architecture.png using matplotlib."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import matplotlib.patheffects as pe
import numpy as np

BG      = '#0D1117'
PANEL   = '#161B22'
BORDER  = '#30363D'
MUTED   = '#8B949E'
WHITE   = '#E6EDF3'

COLORS = {
    'cicd':   '#2196F3',
    'datagen':'#FFB300',
    'raw':    '#00C853',
    'orch':   '#AA00FF',
    'trans':  '#FF6D00',
    'serve':  '#FF1744',
    'infra':  '#546E7A',
}

fig, ax = plt.subplots(figsize=(24, 16))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 24)
ax.set_ylim(0, 16)
ax.axis('off')

def node(ax, x, y, w, h, label, sublabel, color, r=0.25):
    box = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0",
        linewidth=1.2, edgecolor=BORDER,
        facecolor=PANEL, zorder=3)
    ax.add_patch(box)
    # left accent bar
    bar = FancyBboxPatch((x, y + 0.08), 0.06, h - 0.16,
        boxstyle="round,pad=0",
        linewidth=0, facecolor=color, zorder=4)
    ax.add_patch(bar)
    ax.text(x + 0.22, y + h * 0.62, label,
            ha='left', va='center', fontsize=8.5, fontweight='bold',
            color=WHITE, zorder=5)
    if sublabel:
        ax.text(x + 0.22, y + h * 0.28, sublabel,
                ha='left', va='center', fontsize=6.2,
                color=MUTED, zorder=5)

def pill(ax, x, y, w, h, label, color):
    box = FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.12",
        linewidth=1.2, edgecolor=color,
        facecolor=PANEL, zorder=3)
    ax.add_patch(box)
    dot = plt.Circle((x + 0.22, y + h/2), 0.07, color=color, zorder=5)
    ax.add_patch(dot)
    ax.text(x + 0.38, y + h/2, label,
            ha='left', va='center', fontsize=7.5, fontweight='bold',
            color=WHITE, zorder=5)

def arrow(ax, x1, y1, x2, y2, color='#3D444D', lw=1.2, style='->', dashed=True):
    ls = (0, (4, 3)) if dashed else '-'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                        connectionstyle='arc3,rad=0.0'),
        zorder=2)

def layer_header(ax, y, label, color):
    ax.text(0.3, y, label,
            ha='left', va='center', fontsize=8, fontweight='bold',
            color=color, fontstyle='normal',
            letter_spacing=2 if False else 0,
            zorder=5)
    ax.plot([0.3, 23.7], [y - 0.18, y - 0.18], color=BORDER, lw=0.6, zorder=2)

def section_divider(ax, y):
    ax.plot([0.1, 23.9], [y, y], color='#21262D', lw=0.8, linestyle='--', zorder=1)

# ── Title ──────────────────────────────────────────────────────────────────
ax.text(12, 15.5, 'MANDERA ANALYTICS', ha='center', va='center',
        fontsize=28, fontweight='black', color=WHITE, zorder=5)
ax.text(12, 15.0, 'End-to-End Data Pipeline Architecture', ha='center', va='center',
        fontsize=11, color=MUTED, zorder=5)

# gradient bar under title
for i, (k, c) in enumerate(COLORS.items()):
    seg_w = 2.0
    x0 = 12 - len(COLORS) * seg_w / 2 + i * seg_w
    bar = FancyBboxPatch((x0, 14.72), seg_w - 0.04, 0.12,
        boxstyle="round,pad=0", linewidth=0, facecolor=c, zorder=4, alpha=0.9)
    ax.add_patch(bar)

# ── Legend ─────────────────────────────────────────────────────────────────
legend_items = [
    ('CI/CD', COLORS['cicd']), ('Data Gen', COLORS['datagen']),
    ('Raw Storage', COLORS['raw']), ('Orchestration', COLORS['orch']),
    ('Transformation', COLORS['trans']), ('Serving', COLORS['serve']),
    ('Infrastructure', COLORS['infra']),
]
lx = 1.5
for lbl, col in legend_items:
    dot = plt.Circle((lx, 14.3), 0.09, color=col, zorder=5)
    ax.add_patch(dot)
    ax.text(lx + 0.18, 14.3, lbl, ha='left', va='center',
            fontsize=7, fontweight='bold', color=MUTED, zorder=5)
    lx += 2.8 if lbl not in ('Transformation','Infrastructure') else 2.5

# ── LAYER 1 — CI/CD ────────────────────────────────────────────────────────
section_divider(ax, 14.1)
ax.text(0.3, 13.85, '01  CI/CD', ha='left', va='center',
        fontsize=7.5, fontweight='bold', color=COLORS['cicd'], zorder=5)
node(ax, 1.0, 13.0, 3.0, 0.75, 'GitHub', 'Branch: main', COLORS['cicd'])
ax.annotate('', xy=(5.2, 13.38), xytext=(4.0, 13.38),
    arrowprops=dict(arrowstyle='->', color=COLORS['cicd'], lw=1.4), zorder=4)
node(ax, 5.2, 13.0, 4.2, 0.75, 'GitHub Actions',
     '07:00 & 15:00 UTC · workflow_dispatch', COLORS['cicd'])

# ── LAYER 2 — DATA GENERATION ──────────────────────────────────────────────
section_divider(ax, 12.85)
ax.text(0.3, 12.6, '02  DATA GENERATION', ha='left', va='center',
        fontsize=7.5, fontweight='bold', color=COLORS['datagen'], zorder=5)
node(ax, 1.0, 11.7, 5.0, 0.78, 'Python 3.9 + Faker',
     'customers 15–25  ·  orders 3k–6.5k  ·  products 5–10', COLORS['datagen'])
ax.annotate('', xy=(6.0, 12.09), xytext=(9.4, 12.09),
    arrowprops=dict(arrowstyle='<-', color=COLORS['cicd'], lw=1.2), zorder=4)
ax.text(7.5, 12.22, 'triggers', ha='center', fontsize=6.5, color=MUTED, zorder=5)

# ── LAYER 3 — RAW STORAGE ──────────────────────────────────────────────────
section_divider(ax, 11.55)
ax.text(0.3, 11.3, '03  RAW STORAGE', ha='left', va='center',
        fontsize=7.5, fontweight='bold', color=COLORS['raw'], zorder=5)
node(ax, 1.0, 10.35, 3.5, 0.82, 'MongoDB Atlas',
     'mandera_db · customers · orders · products', COLORS['raw'])
ax.annotate('', xy=(5.7, 10.76), xytext=(4.5, 10.76),
    arrowprops=dict(arrowstyle='->', color=COLORS['raw'], lw=1.3), zorder=4)
node(ax, 5.7, 10.35, 3.5, 0.82, 'PostgreSQL 15 — raw',
     'raw.customers · raw.orders · raw.products', COLORS['raw'])
ax.annotate('', xy=(10.4, 10.76), xytext=(9.2, 10.76),
    arrowprops=dict(arrowstyle='->', color=COLORS['raw'], lw=1.3), zorder=4)
node(ax, 10.4, 10.35, 3.5, 0.82, 'MinIO — mandera-raw',
     'customers/ · orders/ · products/ JSON', COLORS['raw'])

# connector from faker down to mongo
ax.annotate('', xy=(2.75, 11.17), xytext=(2.75, 10.35),
    arrowprops=dict(arrowstyle='->', color=COLORS['datagen'], lw=1.2), zorder=4)

# ── LAYER 4 — ORCHESTRATION ────────────────────────────────────────────────
section_divider(ax, 10.2)
ax.text(0.3, 9.95, '04  ORCHESTRATION  ·  Apache Airflow 2.8  ·  LocalExecutor  ·  @daily', ha='left',
        va='center', fontsize=7.5, fontweight='bold', color=COLORS['orch'], zorder=5)

# extract tasks (left col)
node(ax, 1.0, 8.9,  3.4, 0.72, 'extract_to_minio',   'MongoDB → MinIO', COLORS['orch'])
node(ax, 1.0, 8.05, 3.4, 0.72, 'extract_to_postgres','MongoDB → raw.*',  COLORS['orch'])

# parallel transforms (mid col)
node(ax, 6.2, 8.9,  3.4, 0.72, 'transform_customers','raw → staging  [parallel]', COLORS['orch'])
node(ax, 6.2, 8.05, 3.4, 0.72, 'transform_products', 'raw → staging  [parallel]', COLORS['orch'])

# join → orders
node(ax, 11.3, 8.4, 3.6, 0.82, 'transform_orders',
     'sequential (FK: customers + products)', COLORS['orch'])

# truncate
node(ax, 16.6, 8.4, 3.2, 0.82, 'truncate_raw',
     'clears raw.* · data safe in MinIO', COLORS['orch'])

# arrows: extract → parallel
for yfrom, yto in [(9.26, 9.26), (8.41, 8.41)]:
    ax.annotate('', xy=(6.2, yto), xytext=(4.4, yfrom),
        arrowprops=dict(arrowstyle='->', color=COLORS['orch'], lw=1.1), zorder=4)

# parallel → orders
for yfrom in [9.26, 8.41]:
    ax.annotate('', xy=(11.3, 8.81), xytext=(9.6, yfrom),
        arrowprops=dict(arrowstyle='->', color=COLORS['orch'], lw=1.1), zorder=4)

# orders → truncate
ax.annotate('', xy=(16.6, 8.81), xytext=(14.9, 8.81),
    arrowprops=dict(arrowstyle='->', color=COLORS['orch'], lw=1.3), zorder=4)

# fork label
ax.text(5.2, 9.62, 'fork / parallel', ha='center', fontsize=6.5, color=MUTED, zorder=5)
ax.text(10.7, 9.3, 'join >', ha='center', fontsize=6.5, color=MUTED, zorder=5)

# connector from raw storage down to extract tasks
ax.annotate('', xy=(2.7, 9.62), xytext=(2.7, 10.35),
    arrowprops=dict(arrowstyle='<-', color=COLORS['orch'], lw=1.1), zorder=4)
ax.plot([2.7, 2.7], [8.77, 9.62], color=COLORS['orch'], lw=1.1, zorder=3)

# ── LAYER 5 — TRANSFORMATION ───────────────────────────────────────────────
section_divider(ax, 7.85)
ax.text(0.3, 7.6, '05  TRANSFORMATION', ha='left', va='center',
        fontsize=7.5, fontweight='bold', color=COLORS['trans'], zorder=5)
node(ax, 1.0,  6.65, 3.8, 0.82, 'Python Transform Scripts',
     'transform_customers · products · orders · db_utils', COLORS['trans'])
node(ax, 6.0,  6.65, 3.4, 0.82, 'PySpark Notebooks',
     'orders_transform_pyspark · distributed', COLORS['trans'])
node(ax, 11.0, 6.65, 3.4, 0.82, 'JupyterLab',
     '01_raw_exploration · notebooks', COLORS['trans'])

# arrows from truncate down
ax.annotate('', xy=(2.9, 7.47), xytext=(18.2, 8.4),
    arrowprops=dict(arrowstyle='->', color=COLORS['trans'], lw=1.1,
                    connectionstyle='arc3,rad=-0.15'), zorder=4)

# ── LAYER 6 — SERVING ──────────────────────────────────────────────────────
section_divider(ax, 6.5)
ax.text(0.3, 6.25, '06  SERVING', ha='left', va='center',
        fontsize=7.5, fontweight='bold', color=COLORS['serve'], zorder=5)
node(ax, 1.0,  5.28, 4.0, 0.85, 'PostgreSQL 15 — staging',
     'staging.customers · orders · products  |  BI-ready', COLORS['serve'])
node(ax, 6.8,  5.28, 3.8, 0.85, 'MongoDB Atlas',
     'mandera_db · Document store · logging', COLORS['serve'])

# arrow from transform scripts down
ax.annotate('', xy=(3.0, 6.13), xytext=(3.0, 6.65),
    arrowprops=dict(arrowstyle='->', color=COLORS['serve'], lw=1.2), zorder=4)

# ── LAYER 7 — INFRASTRUCTURE ───────────────────────────────────────────────
section_divider(ax, 5.12)
ax.text(0.3, 4.88, '07  INFRASTRUCTURE  ·  Docker Compose  ·  8 services', ha='left',
        va='center', fontsize=7.5, fontweight='bold', color=COLORS['infra'], zorder=5)

pills = ['postgres', 'minio', 'pgadmin', 'jupyter',
         'airflow-init', 'airflow-web', 'airflow-sched', 'db-init']
px = 1.0
for p in pills:
    w = max(1.6, len(p) * 0.16 + 0.8)
    pill(ax, px, 4.1, w, 0.6, p, COLORS['infra'])
    px += w + 0.25

# ── Footer ─────────────────────────────────────────────────────────────────
ax.text(12, 0.35, 'MANDERA ANALYTICS  ·  github.com/chimaojini/MANDERA_ANALYTICS',
        ha='center', va='center', fontsize=7, color='#484F58', zorder=5)

out_dir = os.path.join(os.path.dirname(__file__), 'images')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'architecture.png')
plt.savefig(out_path, dpi=120, bbox_inches='tight',
            facecolor=BG, edgecolor='none')
print(f"Saved: {out_path}")
plt.close()
