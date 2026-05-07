"""
Generate docs/images/architecture.png — MANDERA_ANALYTICS pipeline diagram.
Run once from the repo root: python docs/generate_architecture_png.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ── canvas ────────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 22, 30          # inches  (≈ 2200 × 3000 px @ 100 dpi → export at 100)
DPI = 100
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("#F7F8FA")

# ── colours ───────────────────────────────────────────────────────────────────
C = {
    "cicd":   "#0066CC",
    "gen":    "#F0A500",
    "raw":    "#2E8B57",
    "orch":   "#6A0DAD",
    "trans":  "#E07B00",
    "serve":  "#C0003C",
    "infra":  "#444444",
    "bg":     "#F7F8FA",
    "white":  "#FFFFFF",
    "text":   "#1A1A2E",
    "arrow":  "#555555",
}

ALPHA_LANE = 0.10
ALPHA_BOX  = 0.15
ALPHA_HDR  = 0.85

# ── helper: rounded box ───────────────────────────────────────────────────────
def rbox(ax, x, y, w, h, fc, ec, lw=1.2, alpha=1.0, radius=0.3, zorder=2):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw, edgecolor=ec, facecolor=fc,
        alpha=alpha, zorder=zorder,
    )
    ax.add_patch(patch)
    return patch

def label(ax, x, y, text, fs=8, color="#1A1A2E", bold=False, ha="center", va="center", zorder=5):
    weight = "bold" if bold else "normal"
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va=va,
            fontweight=weight, zorder=zorder,
            fontfamily="DejaVu Sans",
            wrap=False)

def multiline(ax, x, y, lines, fs=7.5, color="#1A1A2E", ha="center", leading=0.28, zorder=5):
    for i, ln in enumerate(lines):
        ax.text(x, y - i * leading, ln, fontsize=fs, color=color,
                ha=ha, va="center", zorder=zorder, fontfamily="DejaVu Sans")

def arrow(ax, x1, y1, x2, y2, color="#555555", lw=1.5, zorder=4):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, mutation_scale=12),
                zorder=zorder)

# ── swim-lane geometry ─────────────────────────────────────────────────────────
#  y goes bottom-to-top in matplotlib, so we define from the TOP of the figure.
MARGIN_L = 0.5
LANE_W   = FIG_W - MARGIN_L - 0.3
HDR_H    = 0.55   # header strip height
GAP      = 0.22   # gap between lanes

lanes = [
    # (label, colour, height)
    ("LAYER 1 — CI/CD",           "cicd",  2.8),
    ("LAYER 2 — DATA GENERATION", "gen",   3.0),
    ("LAYER 3 — RAW STORAGE",     "raw",   3.2),
    ("LAYER 4 — ORCHESTRATION",   "orch",  3.4),
    ("LAYER 5 — TRANSFORMATION",  "trans", 3.4),
    ("LAYER 6 — SERVING",         "raw",   3.2),   # will use serve colour override
    ("LAYER 7 — INFRASTRUCTURE",  "infra", 2.6),
]
# Override colours for L6
LANE_COLOURS = ["cicd","gen","raw","orch","trans","serve","infra"]

# Build top-to-bottom y coordinates
TITLE_H = 0.9
top_y = FIG_H - 0.4 - TITLE_H   # start below title

lane_y = []   # (y_bottom, y_top) for each lane
y = top_y
for i, (lbl, _, h) in enumerate(lanes):
    y_top = y
    y_bot = y - h
    lane_y.append((y_bot, y_top))
    y = y_bot - GAP

# ── TITLE ─────────────────────────────────────────────────────────────────────
ax.text(FIG_W / 2, FIG_H - 0.6,
        "MANDERA_ANALYTICS — End-to-End Data Pipeline Architecture",
        fontsize=16, fontweight="bold", ha="center", va="center",
        color=C["text"], zorder=6)

# ── DRAW LANES ─────────────────────────────────────────────────────────────────
for i, ((y_bot, y_top), (lbl, _, h)) in enumerate(zip(lane_y, lanes)):
    col_key = LANE_COLOURS[i]
    col = C[col_key]
    # background
    rbox(ax, MARGIN_L, y_bot, LANE_W, h, fc=col, ec=col, alpha=ALPHA_LANE, radius=0.4, zorder=1)
    # header strip
    rbox(ax, MARGIN_L, y_top - HDR_H, LANE_W, HDR_H, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.4, zorder=2)
    label(ax, MARGIN_L + LANE_W/2, y_top - HDR_H/2, lbl,
          fs=11, color="white", bold=True, zorder=6)

# ────────────────────────────────────────────────────────────────────────────
# LAYER 1 — CI/CD
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[0]
col = C["cicd"]
cy = (y0 + y1 + HDR_H) / 2   # vertical centre of content area

# GitHub box
gx, gw, gh = MARGIN_L + 1.0, 3.8, 1.8
gy = cy - gh / 2
rbox(ax, gx, gy, gw, gh, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, gx, gy, gw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, gx + gw/2, gy + gh - 0.19, "GitHub / Source Control", fs=9, bold=True, color="white", zorder=6)
multiline(ax, gx + gw/2, gy + gh - 0.62,
          ["Create Branch", "Version Control", "Triggers CI/CD"],
          fs=8, color=C["text"])

# Arrow → GitHub Actions
arrow(ax, gx + gw + 0.1, cy, gx + gw + 1.1, cy, color=col, lw=2)

# GitHub Actions box
ax2 = gx + gw + 1.2
aw, ah = 7.2, 1.8
ay = cy - ah/2
rbox(ax, ax2, ay, aw, ah, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, ax2, ay + ah - 0.38, aw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, ax2 + aw/2, ay + ah - 0.19, "GitHub Actions / CI/CD Trigger", fs=9, bold=True, color="white", zorder=6)
multiline(ax, ax2 + aw/2, ay + ah - 0.65,
          ["Schedules: 07:00 & 13:00–17:00 daily",
           "python on data_generator/generator.py",
           "Runs on: push to main / schedule"],
          fs=8, color=C["text"])

# ────────────────────────────────────────────────────────────────────────────
# LAYER 2 — DATA GENERATION
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[1]
col = C["gen"]
cy = (y0 + y1 + HDR_H) / 2

bx, bw, bh = MARGIN_L + 1.0, LANE_W - 2.0, 2.1
by = cy - bh / 2
rbox(ax, bx, by, bw, bh, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, bx, by + bh - 0.38, bw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, bx + bw/2, by + bh - 0.19,
      "Python 3.9 + Faker — Data Generator", fs=9.5, bold=True, color="white", zorder=6)

# three sub-boxes
sb_w = (bw - 0.6) / 3
sb_h = bh - 0.65
sb_y = by + 0.15
for j, (sname, slines) in enumerate([
    ("fake_customers.py",  ["15–25 customers/batch", "Referential integrity"]),
    ("fake_products.py",   ["3–7 products/batch",    "batch_id, created_at"]),
    ("fake_orders.py",     ["3,000–8,500 orders/batch", "Links cust + prod"]),
]):
    sx = bx + 0.15 + j * (sb_w + 0.15)
    rbox(ax, sx, sb_y, sb_w, sb_h, fc=col, ec=col, alpha=0.25, radius=0.2)
    label(ax, sx + sb_w/2, sb_y + sb_h - 0.22, sname, fs=8.5, bold=True, color=C["text"], zorder=6)
    multiline(ax, sx + sb_w/2, sb_y + sb_h - 0.52, slines, fs=7.5, color=C["text"])

# Arrow down (from layer 2 → 3)
mid_x = MARGIN_L + LANE_W / 2
arrow(ax, mid_x, lane_y[1][0], mid_x, lane_y[2][1] - 0.05, color=C["gen"], lw=2)

# ────────────────────────────────────────────────────────────────────────────
# LAYER 3 — RAW STORAGE (two columns)
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[2]
col = C["raw"]
cy = (y0 + y1 + HDR_H) / 2

half = (LANE_W - 1.2) / 2

# LEFT: PostgreSQL
px = MARGIN_L + 0.5
pw, ph = half, 2.3
py = cy - ph / 2
rbox(ax, px, py, pw, ph, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, px, py + ph - 0.38, pw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, px + pw/2, py + ph - 0.19, "PostgreSQL 15 — raw schema", fs=9, bold=True, color="white", zorder=6)
multiline(ax, px + pw/2, py + ph - 0.62,
          ["raw.customers", "raw.orders", "raw.products", "Via psycopg2 (batch insert)"],
          fs=8, color=C["text"])

# RIGHT: MinIO
mx = px + pw + 0.7
rbox(ax, mx, py, pw, ph, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, mx, py + ph - 0.38, pw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, mx + pw/2, py + ph - 0.19, "MinIO — mandera-raw bucket", fs=9, bold=True, color="white", zorder=6)
multiline(ax, mx + pw/2, py + ph - 0.62,
          ["customers/YYYY-MM-DD/batch_id_k.json",
           "products/YYYY-MM-DD/batch_id_k.json",
           "orders/YYYY-MM-DD/batch_id_k.json",
           "Via boto3 (new JSON written)"],
          fs=7.8, color=C["text"])

# Arrow down (3 → 4)
arrow(ax, mid_x, lane_y[2][0], mid_x, lane_y[3][1] - 0.05, color=C["raw"], lw=2)

# ────────────────────────────────────────────────────────────────────────────
# LAYER 4 — ORCHESTRATION
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[3]
col = C["orch"]
cy_full = (y0 + y1) / 2

# Left sidebar: Airflow info
sbx, sbw, sbh = MARGIN_L + 0.3, 2.8, 2.6
sby = cy_full - sbh / 2
rbox(ax, sbx, sby, sbw, sbh, fc=col, ec=col, alpha=ALPHA_BOX + 0.05, radius=0.3)
rbox(ax, sbx, sby + sbh - 0.38, sbw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, sbx + sbw/2, sby + sbh - 0.19, "Apache Airflow 2.8", fs=8.5, bold=True, color="white", zorder=6)
multiline(ax, sbx + sbw/2, sby + sbh - 0.65,
          ["LocalExecutor", "Schedule: @daily",
           "max_active_runs: 1",
           "Retries: max 2, delay 5 m"],
          fs=7.8, color=C["text"])

# Task flow boxes
tasks = [
    ("extract_to_minio",      ["Uploads JSON", "files to MinIO"]),
    ("extract_to_postgres",   ["Reads raw data", "into PostgreSQL"]),
    ("transform_customers\n+ transform_products", ["[PARALLEL]", "run together"]),
    ("transform_orders",      ["Waits for both", "above tasks"]),
    ("truncate_raw",          ["Clears raw tables", "& raw files"]),
]
tx_start = sbx + sbw + 0.5
tx_avail = LANE_W - (tx_start - MARGIN_L) - 0.3
tw = (tx_avail - 0.2 * (len(tasks) - 1)) / len(tasks)
th = 1.9
ty = cy_full - th / 2

for k, (tname, tlines) in enumerate(tasks):
    tx = tx_start + k * (tw + 0.2)
    is_parallel = k == 2
    fc_alpha = ALPHA_BOX + 0.08 if is_parallel else ALPHA_BOX
    rbox(ax, tx, ty, tw, th, fc=col, ec=col, alpha=fc_alpha, radius=0.25)
    rbox(ax, tx, ty + th - 0.38, tw, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.25, zorder=3)
    # task name (bold, white)
    ax.text(tx + tw/2, ty + th - 0.19, tname,
            fontsize=7.5, fontweight="bold", color="white",
            ha="center", va="center", zorder=6, multialignment="center")
    multiline(ax, tx + tw/2, ty + th - 0.60, tlines, fs=7.2, color=C["text"])
    # arrow to next task
    if k < len(tasks) - 1:
        arrow(ax, tx + tw + 0.01, ty + th/2,
              tx + tw + 0.19, ty + th/2, color=col, lw=1.5)

# Sidebar → first task
arrow(ax, sbx + sbw + 0.01, sby + sbh/2, tx_start - 0.01, ty + th/2, color=col, lw=1.5)

# Arrow down (4 → 5)
arrow(ax, mid_x, lane_y[3][0], mid_x, lane_y[4][1] - 0.05, color=C["orch"], lw=2)

# ────────────────────────────────────────────────────────────────────────────
# LAYER 5 — TRANSFORMATION (three columns)
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[4]
col = C["trans"]
cy = (y0 + y1 + HDR_H) / 2

third = (LANE_W - 1.0) / 3
th5 = 2.3

cols5 = [
    ("Python Transform Scripts",
     ["transform_customers.py",
      "transform_products.py",
      "transform_orders.py",
      "Via db_utils.py (shared)"]),
    ("PySpark Notebooks\n(Distributed transform prototyping)",
     ["orders_transform_pyspark",
      "(customers / products)"]),
    ("JupyterLab Notebooks",
     ["01_raw_exploration.ipynb",
      "customers_transform.ipynb",
      "products_transform.ipynb",
      "orders_transform_pyspark.ipynb"]),
]

for j, (hdr, lines) in enumerate(cols5):
    cx5 = MARGIN_L + 0.3 + j * (third + 0.2)
    cy5 = cy - th5 / 2
    rbox(ax, cx5, cy5, third, th5, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
    rbox(ax, cx5, cy5 + th5 - 0.38, third, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
    ax.text(cx5 + third/2, cy5 + th5 - 0.19, hdr,
            fontsize=8, fontweight="bold", color="white",
            ha="center", va="center", zorder=6, multialignment="center")
    multiline(ax, cx5 + third/2, cy5 + th5 - 0.60, lines, fs=7.5, color=C["text"])

# Arrow down (5 → 6)
arrow(ax, mid_x, lane_y[4][0], mid_x, lane_y[5][1] - 0.05, color=C["trans"], lw=2)

# ────────────────────────────────────────────────────────────────────────────
# LAYER 6 — SERVING (two columns)
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[5]
col = C["serve"]
cy = (y0 + y1 + HDR_H) / 2

half6 = (LANE_W - 1.2) / 2
sh = 2.3

# LEFT: PostgreSQL staging
px6 = MARGIN_L + 0.5
sy = cy - sh / 2
rbox(ax, px6, sy, half6, sh, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, px6, sy + sh - 0.38, half6, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, px6 + half6/2, sy + sh - 0.19, "PostgreSQL 15 — staging schema", fs=9, bold=True, color="white", zorder=6)
multiline(ax, px6 + half6/2, sy + sh - 0.60,
          ["staging.customers (200+ customer_id)",
           "staging.orders (STG product_id)",
           "staging.products (STG: cust, prod)",
           "Ready for BI / analytics / warehouse"],
          fs=7.8, color=C["text"])

# RIGHT: MongoDB Atlas
mx6 = px6 + half6 + 0.7
rbox(ax, mx6, sy, half6, sh, fc=col, ec=col, alpha=ALPHA_BOX, radius=0.3)
rbox(ax, mx6, sy + sh - 0.38, half6, 0.38, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.3, zorder=3)
label(ax, mx6 + half6/2, sy + sh - 0.19, "MongoDB Atlas — Document Store", fs=9, bold=True, color="white", zorder=6)
multiline(ax, mx6 + half6/2, sy + sh - 0.60,
          ["mandera_db database",
           "customers / orders / products collections",
           "Logging + change tracking",
           "Source of truth for raw documents"],
          fs=7.8, color=C["text"])

# Arrow down (6 → 7)
arrow(ax, mid_x, lane_y[5][0], mid_x, lane_y[6][1] - 0.05, color=C["serve"], lw=2)

# ────────────────────────────────────────────────────────────────────────────
# LAYER 7 — INFRASTRUCTURE (Docker Compose service boxes)
# ────────────────────────────────────────────────────────────────────────────
(y0, y1) = lane_y[6]
col = C["infra"]
cy7 = (y0 + y1 + HDR_H) / 2

services = ["postgres","minio","pgadmin","jupyter","airflow-init","airflow-web","airflow-sched","db-init"]
n = len(services)
srv_w = (LANE_W - 1.2) / n - 0.1
srv_h = 1.2
srv_y = cy7 - srv_h / 2

for k, svc in enumerate(services):
    sx7 = MARGIN_L + 0.5 + k * (srv_w + 0.12)
    rbox(ax, sx7, srv_y, srv_w, srv_h, fc=col, ec=col, alpha=ALPHA_BOX + 0.1, radius=0.2)
    rbox(ax, sx7, srv_y + srv_h - 0.32, srv_w, 0.32, fc=col, ec=col, alpha=ALPHA_HDR, radius=0.2, zorder=3)
    label(ax, sx7 + srv_w/2, srv_y + srv_h - 0.16, svc, fs=7.5, bold=True, color="white", zorder=6)

# Docker Compose header label
label(ax, MARGIN_L + 1.2, (y0 + y1)/2 - 0.3 + HDR_H,
      "Docker Compose — 8 services", fs=8, bold=False, color=C["infra"],
      ha="left", zorder=6)

# ────────────────────────────────────────────────────────────────────────────
# LEGEND (top-right)
# ────────────────────────────────────────────────────────────────────────────
leg_x = FIG_W - 4.5
leg_y = FIG_H - 1.0
leg_w = 4.0
leg_h = 3.2

rbox(ax, leg_x, leg_y - leg_h, leg_w, leg_h, fc="white", ec="#CCCCCC", alpha=0.95, radius=0.3, zorder=7)
label(ax, leg_x + leg_w/2, leg_y - 0.25, "Pipeline Layers", fs=9, bold=True, color=C["text"], zorder=8)

legend_items = [
    ("CI/CD",           "cicd"),
    ("Data Generation", "gen"),
    ("Raw Storage",     "raw"),
    ("Orchestration",   "orch"),
    ("Transformation",  "trans"),
    ("Serving",         "serve"),
    ("Infrastructure",  "infra"),
]
for i, (lbl, ckey) in enumerate(legend_items):
    ly = leg_y - 0.58 - i * 0.36
    swatch = FancyBboxPatch((leg_x + 0.2, ly - 0.12), 0.45, 0.26,
                            boxstyle="round,pad=0,rounding_size=0.05",
                            facecolor=C[ckey], edgecolor="none", zorder=8)
    ax.add_patch(swatch)
    label(ax, leg_x + 0.85, ly + 0.01, lbl, fs=8.5, color=C["text"], ha="left", zorder=8)

# ── save ──────────────────────────────────────────────────────────────────────
import os, pathlib
out = pathlib.Path(__file__).parent / "images" / "architecture.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {out}  ({out.stat().st_size // 1024} KB)")
