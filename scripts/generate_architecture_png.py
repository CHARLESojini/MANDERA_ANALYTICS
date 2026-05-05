"""
Generate docs/images/architecture.png — a standalone, publication-quality
architecture diagram for the MANDERA_ANALYTICS pipeline.

No external data sources required; uses only matplotlib + standard library.
Run from the repo root:
    python scripts/generate_architecture_png.py
"""

import os
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

# ─── canvas ────────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 22, 17   # inches  →  2200 × 1700 px @ 100 dpi
DPI = 100

# ─── colour palette ────────────────────────────────────────────────────────────
LAYER_FILL = {
    "cicd":   "#DAE8FC",
    "gen":    "#FFF2CC",
    "raw":    "#D5E8D4",
    "orch":   "#E1D5E7",
    "xform":  "#FFE6CC",
    "serve":  "#F8CECC",
    "infra":  "#F5F5F5",
}
LAYER_EDGE = {
    "cicd":  "#6C8EBF",
    "gen":   "#D6B656",
    "raw":   "#82B366",
    "orch":  "#9673A6",
    "xform": "#D79B00",
    "serve": "#B85450",
    "infra": "#666666",
}
TASK_FILL   = "#D9B3F0"
TASK_EDGE   = "#9673A6"
TASK_LATE   = "#9B59B6"
TASK_LATE_EDGE = "#7D3C98"
TRUNC_FILL  = "#E8DAEF"
ARROW_COL   = "#444444"

# ─── layer geometry (x, y, w, h) in data units (0–22 wide, 0–17 tall) ─────────
# We flip y so 0=top; matplotlib uses 0=bottom so we subtract from FIG_H.
# All coordinates are in data units on a 22×17 canvas.

LAYERS = [
    # key       label                              x      y      w      h
    ("cicd",  "Layer 1 — CI/CD & Source Control",  0.3,  16.2,  21.4,  1.5),
    ("gen",   "Layer 2 — Data Generation",          0.3,  14.4,  21.4,  1.5),
    ("raw",   "Layer 3 — Raw Storage",              0.3,  12.4,  21.4,  1.7),
    ("orch",  "Layer 4 — Orchestration (Apache Airflow DAG)", 0.3, 9.2, 21.4, 2.95),
    ("xform", "Layer 5 — Transformation (Scripts + PySpark + Jupyter)", 0.3, 7.1, 21.4, 1.85),
    ("serve", "Layer 6 — Serving Layer",            0.3,  4.9,   21.4,  1.95),
    ("infra", "Layer 7 — Infrastructure (Docker / Docker Compose)", 0.3, 2.8, 21.4, 1.85),
]


def add_layer(ax, key, label, x, y, w, h):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03",
        linewidth=1.5,
        edgecolor=LAYER_EDGE[key],
        facecolor=LAYER_FILL[key],
        zorder=1,
    )
    ax.add_patch(rect)
    ax.text(
        x + 0.15, y + h - 0.07, label,
        fontsize=9.5, fontweight="bold",
        va="top", ha="left", color="#1a1a2e",
        zorder=3,
    )


def box(ax, x, y, w, h, label, fc, ec, fs=8.5, bold=False, zorder=4):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04",
        linewidth=1.2,
        edgecolor=ec,
        facecolor=fc,
        zorder=zorder,
    )
    ax.add_patch(rect)
    weight = "bold" if bold else "normal"
    ax.text(
        x + w / 2, y + h / 2, label,
        fontsize=fs, fontweight=weight,
        va="center", ha="center", color="#1a1a2e",
        multialignment="center", wrap=True,
        zorder=zorder + 1,
    )
    return (x + w / 2, y + h / 2)   # centre point


def arrow(ax, x0, y0, x1, y1, label="", col=ARROW_COL, lw=1.5, style="->",
          connectionstyle="arc3,rad=0.0"):
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle=style, color=col, lw=lw,
            connectionstyle=connectionstyle,
        ),
        zorder=5,
    )
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(mx, my, label, fontsize=7, color=col,
                ha="center", va="center",
                bbox=dict(fc="white", ec="none", pad=1),
                zorder=6)


def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # ── title ──────────────────────────────────────────────────────────────────
    ax.text(
        11, 16.9,
        "MANDERA_ANALYTICS — End-to-End Data Pipeline Architecture",
        fontsize=14, fontweight="bold", ha="center", va="center",
        color="#1a1a2e", zorder=10,
    )

    # ── draw layer backgrounds ──────────────────────────────────────────────────
    for key, label, x, y, w, h in LAYERS:
        add_layer(ax, key, label, x, y, w, h)

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 1 — CI/CD  (y=16.2..17.7)
    # ═══════════════════════════════════════════════════════════════════════════
    L1Y = 16.35

    # GitHub
    box(ax, 1.0, L1Y, 2.0, 1.1,
        "GitHub\nSource Control\n(main branch)",
        "#bdd7f5", LAYER_EDGE["cicd"], fs=8.5, bold=True)

    # GitHub Actions
    box(ax, 3.6, L1Y, 4.2, 1.1,
        "GitHub Actions  ⚡\nCI/CD Trigger\nSchedule: 07:00 & 15:00 UTC daily\npython -m Data_Generator.generator",
        "#bdd7f5", LAYER_EDGE["cicd"], fs=8)

    gh_mid   = (2.0, L1Y + 0.55)
    gha_mid  = (3.6, L1Y + 0.55)
    arrow(ax, gh_mid[0], gh_mid[1], gha_mid[0], gha_mid[1],
          col=LAYER_EDGE["cicd"], lw=2)

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 2 — Data Generation  (y=14.4..15.9)
    # ═══════════════════════════════════════════════════════════════════════════
    L2Y = 14.55

    box(ax, 2.5, L2Y, 6.5, 1.1,
        "Python 3.9+ + Faker — Data Generator\n"
        "fake_customers.py → 15–25 customers/batch\n"
        "fake_products.py  →  5–10 products/batch\n"
        "fake_orders.py    →  3 000–6 500 orders/batch\n"
        "Each record tagged with batch_id + created_at",
        "#ffeea0", LAYER_EDGE["gen"], fs=8.5)
    gen_cx, gen_cy = 5.75, L2Y + 0.55

    # GitHub Actions → generator
    arrow(ax, 4.5, L1Y, 4.5, L2Y + 1.1,
          label="triggers", col=LAYER_EDGE["gen"], lw=2)

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 3 — Raw Storage  (y=12.4..14.1)
    # ═══════════════════════════════════════════════════════════════════════════
    L3Y = 12.55

    # PostgreSQL raw
    box(ax, 1.2, L3Y, 3.8, 1.3,
        "PostgreSQL 15 — raw schema\n\nraw.customers\nraw.orders\nraw.products\n(no transformation; bulk-inserted)",
        "#b5d6b2", LAYER_EDGE["raw"], fs=8.5)
    pg_raw_cx, pg_raw_cy = 3.1, L3Y + 0.65

    # MinIO
    box(ax, 6.0, L3Y, 4.5, 1.3,
        "MinIO — mandera-raw bucket\n\ncustomers/YYYY-MM-DD/batch_N.json\nproducts/YYYY-MM-DD/batch_N.json\norders/YYYY-MM-DD/batch_N.json\nDurable raw JSON archive",
        "#b5d6b2", LAYER_EDGE["raw"], fs=8.5)
    minio_cx, minio_cy = 8.25, L3Y + 0.65

    # generator → PostgreSQL raw
    arrow(ax, gen_cx, L2Y, pg_raw_cx, L3Y + 1.3,
          label="inserts batch", col=LAYER_EDGE["raw"], lw=2)

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 4 — Orchestration  (y=9.2..12.15)
    # ═══════════════════════════════════════════════════════════════════════════
    L4Y = 9.35

    # Airflow sidebar
    box(ax, 0.5, L4Y, 2.2, 2.6,
        "Apache Airflow 2.8\nLocalExecutor\n\n"
        "DAG:\nmandera_analytics\n_pipeline\n\n"
        "Schedule:\n30 7,15 * * *\n\n"
        "max_active_runs=1\nRetries: 2 × 5 min",
        "#e8d5f5", LAYER_EDGE["orch"], fs=8, bold=True)

    # DAG task container
    dag_box = FancyBboxPatch(
        (2.9, L4Y), 18.5, 2.6,
        boxstyle="round,pad=0.04",
        linewidth=1, linestyle="dashed",
        edgecolor=LAYER_EDGE["orch"],
        facecolor="#f3ecfc",
        zorder=2,
    )
    ax.add_patch(dag_box)
    ax.text(3.1, L4Y + 2.52, "DAG Task Graph  →  mandera_analytics_pipeline",
            fontsize=8, fontstyle="italic", color="#5b2c8d", zorder=3)

    # Extract tasks (column 1)
    TH = 0.85  # task box height
    TW = 3.0   # task box width

    # extract_to_minio
    box(ax, 3.2, L4Y + 1.6, TW, TH,
        "extract_to_minio\nPostgreSQL raw → MinIO\nUploads dated JSON files",
        TASK_FILL, TASK_EDGE, fs=8, bold=True)
    etm_cx, etm_cy = 3.2 + TW/2, L4Y + 1.6 + TH/2

    # extract_to_postgres
    box(ax, 3.2, L4Y + 0.5, TW, TH,
        "extract_to_postgres\nReads raw PostgreSQL schema\nPrepares data for transforms",
        TASK_FILL, TASK_EDGE, fs=8, bold=True)
    etp_cx, etp_cy = 3.2 + TW/2, L4Y + 0.5 + TH/2

    # transform_customers (column 2, top)
    box(ax, 7.4, L4Y + 1.6, TW, TH,
        "transform_customers\nValidate + clean customers\nLoad staging.customers",
        "#c39bd3", TASK_EDGE, fs=8, bold=True)
    tc_cx, tc_cy = 7.4 + TW/2, L4Y + 1.6 + TH/2

    # transform_products (column 2, bottom)
    box(ax, 7.4, L4Y + 0.5, TW, TH,
        "transform_products\nValidate + clean products\nLoad staging.products",
        "#c39bd3", TASK_EDGE, fs=8, bold=True)
    tp_cx, tp_cy = 7.4 + TW/2, L4Y + 0.5 + TH/2

    ax.text(7.4 + TW/2, L4Y + 1.48, "⟨ PARALLEL ⟩",
            fontsize=8, fontstyle="italic", color=TASK_EDGE,
            ha="center", va="center", zorder=5)

    # transform_orders (column 3)
    box(ax, 11.7, L4Y + 0.9, TW, TH,
        "transform_orders\nWaits: customers + products done\nFK constraints enforced\nLoad staging.orders",
        TASK_LATE, TASK_LATE_EDGE, fs=8, bold=True)
    to_cx, to_cy = 11.7 + TW/2, L4Y + 0.9 + TH/2
    # override text colour to white for dark bg
    ax.texts[-1].set_color("white")

    # truncate_raw (column 4)
    box(ax, 16.0, L4Y + 1.1, TW, 0.75,
        "truncate_raw\nClears raw.* tables\nRaw data safe in MinIO",
        TRUNC_FILL, TASK_EDGE, fs=8, bold=True)
    tr_cx, tr_cy = 16.0 + TW/2, L4Y + 1.1 + 0.375

    # ── intra-DAG arrows ──────────────────────────────────────────────
    # extract → transform_customers
    arrow(ax, etm_cx + TW/2 - 0.3, etm_cy, 7.4, tc_cy,
          col=TASK_EDGE, lw=1.5)
    arrow(ax, etp_cx + TW/2 - 0.3, etp_cy, 7.4, tp_cy,
          col=TASK_EDGE, lw=1.5)
    # cross-extract → transforms (fan-in)
    arrow(ax, etm_cx + TW/2 - 0.3, etm_cy, 7.4, tp_cy,
          col=TASK_EDGE, lw=1, connectionstyle="arc3,rad=0.12")
    arrow(ax, etp_cx + TW/2 - 0.3, etp_cy, 7.4, tc_cy,
          col=TASK_EDGE, lw=1, connectionstyle="arc3,rad=-0.12")
    # transforms → transform_orders
    arrow(ax, 7.4 + TW, tc_cy, 11.7, to_cy,
          col=TASK_LATE_EDGE, lw=1.5)
    arrow(ax, 7.4 + TW, tp_cy, 11.7, to_cy,
          col=TASK_LATE_EDGE, lw=1.5)
    # transform_orders → truncate_raw
    arrow(ax, 11.7 + TW, to_cy, 16.0, tr_cy,
          col=TASK_EDGE, lw=1.5)

    # ── cross-layer arrows INTO layer 4 ──────────────────────────────
    # PostgreSQL raw → extract_to_minio
    arrow(ax, pg_raw_cx, L3Y, etm_cx, L4Y + 1.6 + TH,
          label="reads raw", col=LAYER_EDGE["orch"], lw=2)
    # PostgreSQL raw → extract_to_postgres
    arrow(ax, pg_raw_cx - 0.5, L3Y, etp_cx, L4Y + 0.5 + TH,
          label="reads raw", col=LAYER_EDGE["orch"], lw=2,
          connectionstyle="arc3,rad=0.15")
    # extract_to_minio → MinIO (back up to layer 3)
    arrow(ax, etm_cx, L4Y + 1.6 + TH, minio_cx, L3Y,
          label="uploads JSON", col=LAYER_EDGE["raw"], lw=2,
          connectionstyle="arc3,rad=-0.25")

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 5 — Transformation  (y=7.1..8.95)
    # ═══════════════════════════════════════════════════════════════════════════
    L5Y = 7.25

    box(ax, 1.2, L5Y, 4.5, 1.4,
        "Python Transform Scripts\n\ntransform_customers.py\ntransform_products.py\ntransform_orders.py\ndb_utils.py (shared helpers)",
        "#ffcc99", LAYER_EDGE["xform"], fs=8.5)

    box(ax, 6.5, L5Y, 4.5, 1.4,
        "PySpark\n\norders_transform_pyspark.ipynb\nDistributed transform prototyping\nJupyterLab PySpark kernel",
        "#ffcc99", LAYER_EDGE["xform"], fs=8.5)

    box(ax, 11.8, L5Y, 5.0, 1.4,
        "JupyterLab Notebooks\n\n01_raw_exploration.ipynb\ncustomers_transform.ipynb\nproducts_transform.ipynb\nload_staging.ipynb",
        "#ffcc99", LAYER_EDGE["xform"], fs=8.5)

    # dashed reference arrow: Python scripts ↔ Airflow transform tasks
    arrow(ax, 3.45, L5Y + 1.4, tc_cx, L4Y + 1.6,
          label="implements", col=LAYER_EDGE["xform"], lw=1,
          style="<->")

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 6 — Serving Layer  (y=4.9..6.85)
    # ═══════════════════════════════════════════════════════════════════════════
    L6Y = 5.05

    # PostgreSQL staging
    box(ax, 1.2, L6Y, 5.2, 1.55,
        "PostgreSQL 15 — staging schema\n\n"
        "staging.customers   (PK: customer_id)\n"
        "staging.products    (PK: product_id)\n"
        "staging.orders      (FK → customers, products)\n\n"
        "Referential integrity enforced\nReady for BI / analytics / warehouse",
        "#f4b8b5", LAYER_EDGE["serve"], fs=8.5)
    pg_stg_cx, pg_stg_cy = 3.8, L6Y + 0.775

    # MongoDB Atlas
    box(ax, 7.8, L6Y, 5.2, 1.55,
        "MongoDB Atlas — Document Store\n\n"
        "mandera_db database\n"
        "customers | products | orders collections\n\n"
        "batch_id lineage tracking\n"
        "Source of truth for raw documents",
        "#f4b8b5", LAYER_EDGE["serve"], fs=8.5)
    mongo_cx = 10.4

    # arrows from transform tasks → staging
    arrow(ax, tc_cx, L4Y + 1.6, pg_stg_cx - 0.5, L6Y + 1.55,
          label="staging.customers", col=LAYER_EDGE["serve"], lw=1.5)
    arrow(ax, tp_cx, L4Y + 0.5, pg_stg_cx, L6Y + 1.55,
          label="staging.products", col=LAYER_EDGE["serve"], lw=1.5,
          connectionstyle="arc3,rad=0.1")
    arrow(ax, to_cx, L4Y + 0.9, pg_stg_cx + 0.5, L6Y + 1.55,
          label="staging.orders", col=LAYER_EDGE["serve"], lw=1.5,
          connectionstyle="arc3,rad=-0.05")

    # PostgreSQL staging → MongoDB Atlas
    arrow(ax, 1.2 + 5.2, pg_stg_cy, 7.8, pg_stg_cy,
          label="document records", col=LAYER_EDGE["serve"], lw=2)

    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 7 — Infrastructure  (y=2.8..4.65)
    # ═══════════════════════════════════════════════════════════════════════════
    L7Y = 2.95

    ax.text(0.7, L7Y + 1.65, "Docker\nCompose\n8 services",
            fontsize=8.5, fontweight="bold", va="center", ha="center",
            color=LAYER_EDGE["infra"], zorder=5)

    SERVICES = [
        "postgres\n(:5438 host)",
        "minio\n(:9000 API\n:9001 Console)",
        "pgadmin\n(:5050)",
        "jupyter\n(:8888)",
        "airflow-init\n(setup)",
        "airflow-\nwebserver\n(:8080)",
        "airflow-\nscheduler",
        "db-init\n(creates\nairflow_db)",
    ]
    sw = 2.3
    gap = 0.15
    start_x = 1.5
    for i, svc in enumerate(SERVICES):
        bx = start_x + i * (sw + gap)
        box(ax, bx, L7Y + 0.35, sw, 1.3,
            svc, "#e0e0e0", LAYER_EDGE["infra"], fs=8)

    ax.text(0.5, L7Y + 0.1,
            "All local services containerised via docker-compose.yml.  "
            "Volumes persist data between restarts.  .env supplies all credentials.",
            fontsize=7.5, fontstyle="italic", color="#666666",
            va="bottom", ha="left", zorder=5)

    # ── legend ─────────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(facecolor=LAYER_FILL["cicd"],  edgecolor=LAYER_EDGE["cicd"],  label="CI/CD"),
        mpatches.Patch(facecolor=LAYER_FILL["gen"],   edgecolor=LAYER_EDGE["gen"],   label="Data Generation"),
        mpatches.Patch(facecolor=LAYER_FILL["raw"],   edgecolor=LAYER_EDGE["raw"],   label="Raw Storage"),
        mpatches.Patch(facecolor=LAYER_FILL["orch"],  edgecolor=LAYER_EDGE["orch"],  label="Orchestration"),
        mpatches.Patch(facecolor=LAYER_FILL["xform"], edgecolor=LAYER_EDGE["xform"], label="Transformation"),
        mpatches.Patch(facecolor=LAYER_FILL["serve"], edgecolor=LAYER_EDGE["serve"], label="Serving"),
        mpatches.Patch(facecolor=LAYER_FILL["infra"], edgecolor=LAYER_EDGE["infra"], label="Infrastructure"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower right",
        fontsize=8,
        framealpha=0.9,
        title="Layers",
        title_fontsize=9,
    )

    # ── save ───────────────────────────────────────────────────────────────────
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "images")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "architecture.png")
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight", facecolor="white")
    print(f"Saved: {os.path.abspath(out_path)}")
    plt.close(fig)


if __name__ == "__main__":
    main()
