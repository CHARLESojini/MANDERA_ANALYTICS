"""
Generate docs/architecture.drawio — mxGraph XML for MANDERA_ANALYTICS pipeline.
Run once from the repo root: python docs/generate_drawio.py
"""
import pathlib, textwrap

# ── id counter ────────────────────────────────────────────────────────────────
_id = 1
def nid():
    global _id
    _id += 1
    return str(_id)

# ── colour palette ────────────────────────────────────────────────────────────
C = {
    "cicd":  "#0066CC",
    "gen":   "#F0A500",
    "raw":   "#2E8B57",
    "orch":  "#6A0DAD",
    "trans": "#E07B00",
    "serve": "#C0003C",
    "infra": "#444444",
}

# ── style helpers ─────────────────────────────────────────────────────────────
def lane_bg(color):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};"
        f"fillOpacity=12;strokeOpacity=40;"
        f"fontSize=10;fontColor=#1A1A2E;verticalAlign=top;"
    )

def lane_hdr(color):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};"
        f"fillOpacity=90;strokeOpacity=90;"
        f"fontSize=13;fontStyle=1;fontColor=#FFFFFF;verticalAlign=middle;"
    )

def box_bg(color):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};"
        f"fillOpacity=18;strokeOpacity=60;"
        f"fontSize=10;fontColor=#1A1A2E;verticalAlign=top;"
    )

def box_hdr(color):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};"
        f"fillOpacity=90;strokeOpacity=90;"
        f"fontSize=10;fontStyle=1;fontColor=#FFFFFF;verticalAlign=middle;"
    )

def sub_box(color):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};"
        f"fillOpacity=25;strokeOpacity=60;"
        f"fontSize=9;fontColor=#1A1A2E;verticalAlign=middle;"
    )

def svc_box(color):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};"
        f"fillOpacity=25;strokeOpacity=60;"
        f"fontSize=9;fontStyle=1;fontColor=#FFFFFF;verticalAlign=middle;"
    )

def arrow_style(color):
    return (
        f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        f"jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
        f"entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
        f"strokeColor={color};fillColor={color};strokeWidth=2;"
    )

def varrow_style(color):
    return (
        f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        f"jettySize=auto;exitX=0.5;exitY=1;exitDx=0;exitDy=0;"
        f"entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
        f"strokeColor={color};fillColor={color};strokeWidth=2.5;"
    )

# ── XML building blocks ───────────────────────────────────────────────────────
def rect(cid, parent, label, style, x, y, w, h):
    lbl = label.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')
    return (
        f'<mxCell id="{cid}" value="{lbl}" style="{style}" '
        f'vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
        f'</mxCell>\n'
    )

def edge(cid, parent, src, tgt, style, label=""):
    lbl = label.replace("&","&amp;")
    return (
        f'<mxCell id="{cid}" value="{lbl}" style="{style}" '
        f'edge="1" source="{src}" target="{tgt}" parent="{parent}">'
        f'<mxGeometry relative="1" as="geometry"/>'
        f'</mxCell>\n'
    )

# ── layout constants ──────────────────────────────────────────────────────────
ML = 40          # left margin
TW = 2200        # total canvas width
CW = TW - ML*2  # content width = 2120
HDR = 40         # lane header height
BOX_HDR = 32     # box header height
GAP = 20         # gap between lanes

# Lane y positions and heights
TITLE_H = 60
L1_Y, L1_H = 90,  200
L2_Y, L2_H = L1_Y+L1_H+GAP, 250
L3_Y, L3_H = L2_Y+L2_H+GAP, 270
L4_Y, L4_H = L3_Y+L3_H+GAP, 290
L5_Y, L5_H = L4_Y+L4_H+GAP, 285
L6_Y, L6_H = L5_Y+L5_H+GAP, 270
L7_Y, L7_H = L6_Y+L6_H+GAP, 210

TOTAL_H = L7_Y + L7_H + 50

cells = []

# ── TITLE ─────────────────────────────────────────────────────────────────────
t_id = nid()
cells.append(rect(
    t_id, "1",
    "MANDERA_ANALYTICS — End-to-End Data Pipeline Architecture",
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#1A1A2E;strokeColor=#1A1A2E;"
    "fontSize=18;fontStyle=1;fontColor=#FFFFFF;verticalAlign=middle;",
    ML, 20, CW, TITLE_H,
))

# ── LEGEND ────────────────────────────────────────────────────────────────────
leg_x = TW - 320
leg_y = 100
leg_w = 280
leg_h = 290
leg_id = nid()
cells.append(rect(
    leg_id, "1", "",
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CCCCCC;"
    "fillOpacity=95;fontSize=10;",
    leg_x, leg_y, leg_w, leg_h,
))
leg_hdr_id = nid()
cells.append(rect(
    leg_hdr_id, "1", "Pipeline Layers",
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#1A1A2E;strokeColor=#1A1A2E;"
    "fontSize=11;fontStyle=1;fontColor=#FFFFFF;",
    leg_x+10, leg_y+10, leg_w-20, 30,
))
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
    sy = leg_y + 52 + i * 32
    sw_id = nid()
    cells.append(rect(
        sw_id, "1", "",
        f"rounded=1;whiteSpace=wrap;html=1;fillColor={C[ckey]};strokeColor={C[ckey]};",
        leg_x+15, sy+2, 30, 22,
    ))
    txt_id = nid()
    cells.append(rect(
        txt_id, "1", lbl,
        "text;html=1;align=left;verticalAlign=middle;resizable=0;"
        "points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=10;",
        leg_x+55, sy, 200, 26,
    ))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — CI/CD
# ─────────────────────────────────────────────────────────────────────────────
col = C["cicd"]
l1_bg = nid()
cells.append(rect(l1_bg, "1", "", lane_bg(col), ML, L1_Y, CW, L1_H))
l1_hdr = nid()
cells.append(rect(l1_hdr, "1", "LAYER 1 — CI/CD", lane_hdr(col), ML, L1_Y, CW, HDR))

# GitHub box
gh_x, gh_y, gh_w, gh_h = ML+60, L1_Y+HDR+15, 340, L1_H-HDR-30
gh_id = nid()
cells.append(rect(gh_id, "1", "", box_bg(col), gh_x, gh_y, gh_w, gh_h))
gh_hdr_id = nid()
cells.append(rect(gh_hdr_id, "1", "GitHub / Source Control", box_hdr(col),
                  gh_x, gh_y, gh_w, BOX_HDR))
gh_body_id = nid()
cells.append(rect(gh_body_id, "1",
                  "Create Branch&#xa;Version Control&#xa;Triggers CI/CD",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=10;",
                  gh_x, gh_y+BOX_HDR, gh_w, gh_h-BOX_HDR))

# GitHub Actions box
ga_x, ga_y = gh_x + gh_w + 120, L1_Y+HDR+10
ga_w, ga_h = CW - (gh_x-ML) - gh_w - 180, L1_H-HDR-20
ga_id = nid()
cells.append(rect(ga_id, "1", "", box_bg(col), ga_x, ga_y, ga_w, ga_h))
ga_hdr_id = nid()
cells.append(rect(ga_hdr_id, "1", "GitHub Actions / CI/CD Trigger", box_hdr(col),
                  ga_x, ga_y, ga_w, BOX_HDR))
ga_body_id = nid()
cells.append(rect(ga_body_id, "1",
                  "Schedules: 07:00 &amp; 13:00–17:00 daily&#xa;"
                  "python on data_generator/generator.py&#xa;"
                  "Triggers: push to main / cron schedule",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=10;",
                  ga_x, ga_y+BOX_HDR, ga_w, ga_h-BOX_HDR))

# Arrow GitHub → Actions
arr_gh_ga = nid()
cells.append(edge(arr_gh_ga, "1", gh_id, ga_id,
                  arrow_style(col)+"exitX=1;exitY=0.5;entryX=0;entryY=0.5;"))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — DATA GENERATION
# ─────────────────────────────────────────────────────────────────────────────
col = C["gen"]
l2_bg = nid()
cells.append(rect(l2_bg, "1", "", lane_bg(col), ML, L2_Y, CW, L2_H))
l2_hdr = nid()
cells.append(rect(l2_hdr, "1", "LAYER 2 — DATA GENERATION", lane_hdr(col), ML, L2_Y, CW, HDR))

# Main generator box
mg_x, mg_y, mg_w, mg_h = ML+40, L2_Y+HDR+10, CW-80, L2_H-HDR-20
mg_id = nid()
cells.append(rect(mg_id, "1", "", box_bg(col), mg_x, mg_y, mg_w, mg_h))
mg_hdr_id = nid()
cells.append(rect(mg_hdr_id, "1", "Python 3.9 + Faker — Data Generator", box_hdr(col),
                  mg_x, mg_y, mg_w, BOX_HDR))

# Sub-boxes
sub_labels = [
    ("fake_customers.py", "15–25 customers / batch&#xa;Referential integrity&#xa;(batch_id, created_at)"),
    ("fake_products.py",  "3–7 products / batch&#xa;Referential integrity&#xa;(batch_id, created_at)"),
    ("fake_orders.py",    "3,000–8,500 orders / batch&#xa;Links customers + products&#xa;batch_id, created_at"),
]
sub_w = (mg_w - 60) // 3 - 10
sub_h = mg_h - BOX_HDR - 25
for k, (sh, sbody) in enumerate(sub_labels):
    sx = mg_x + 20 + k * (sub_w + 15)
    sy = mg_y + BOX_HDR + 12
    sb_id = nid()
    cells.append(rect(sb_id, "1", f"&lt;b&gt;{sh}&lt;/b&gt;&#xa;{sbody}",
                      sub_box(col), sx, sy, sub_w, sub_h))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — RAW STORAGE
# ─────────────────────────────────────────────────────────────────────────────
col = C["raw"]
l3_bg = nid()
cells.append(rect(l3_bg, "1", "", lane_bg(col), ML, L3_Y, CW, L3_H))
l3_hdr = nid()
cells.append(rect(l3_hdr, "1", "LAYER 3 — RAW STORAGE", lane_hdr(col), ML, L3_Y, CW, HDR))

half3 = (CW - 80) // 2 - 10
r3_y = L3_Y + HDR + 15
r3_h = L3_H - HDR - 30

# PostgreSQL
pg_id = nid()
cells.append(rect(pg_id, "1", "", box_bg(col), ML+40, r3_y, half3, r3_h))
pg_hdr_id = nid()
cells.append(rect(pg_hdr_id, "1", "PostgreSQL 15 — raw schema", box_hdr(col),
                  ML+40, r3_y, half3, BOX_HDR))
pg_body_id = nid()
cells.append(rect(pg_body_id, "1",
                  "raw.customers&#xa;raw.orders&#xa;raw.products&#xa;Via psycopg2 (batch insert)",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=10;",
                  ML+40, r3_y+BOX_HDR, half3, r3_h-BOX_HDR))

# MinIO
mn_x = ML+40 + half3 + 20
mn_id = nid()
cells.append(rect(mn_id, "1", "", box_bg(col), mn_x, r3_y, half3, r3_h))
mn_hdr_id = nid()
cells.append(rect(mn_hdr_id, "1", "MinIO — mandera-raw bucket", box_hdr(col),
                  mn_x, r3_y, half3, BOX_HDR))
mn_body_id = nid()
cells.append(rect(mn_body_id, "1",
                  "customers/YYYY-MM-DD/batch_id_k.json&#xa;"
                  "products/YYYY-MM-DD/batch_id_k.json&#xa;"
                  "orders/YYYY-MM-DD/batch_id_k.json&#xa;"
                  "Via boto3 (new JSON written)",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=10;",
                  mn_x, r3_y+BOX_HDR, half3, r3_h-BOX_HDR))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 4 — ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────
col = C["orch"]
l4_bg = nid()
cells.append(rect(l4_bg, "1", "", lane_bg(col), ML, L4_Y, CW, L4_H))
l4_hdr = nid()
cells.append(rect(l4_hdr, "1", "LAYER 4 — ORCHESTRATION", lane_hdr(col), ML, L4_Y, CW, HDR))

# Airflow sidebar
af_x, af_y, af_w, af_h = ML+30, L4_Y+HDR+15, 230, L4_H-HDR-30
af_id = nid()
cells.append(rect(af_id, "1", "", box_bg(col), af_x, af_y, af_w, af_h))
af_hdr_id = nid()
cells.append(rect(af_hdr_id, "1", "Apache Airflow 2.8", box_hdr(col),
                  af_x, af_y, af_w, BOX_HDR))
af_body_id = nid()
cells.append(rect(af_body_id, "1",
                  "LocalExecutor&#xa;Schedule: @daily&#xa;"
                  "max_active_runs: 1&#xa;Retries: max 2, delay 5 m",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=9.5;",
                  af_x, af_y+BOX_HDR, af_w, af_h-BOX_HDR))

# Task flow boxes
tasks = [
    ("extract_to_minio",        "Uploads JSON files&#xa;to MinIO object storage"),
    ("extract_to_postgres",     "Reads from MongoDB&#xa;Inserts to raw schema"),
    ("[PARALLEL]&#xa;transform_customers&#xa;+ transform_products", "Run concurrently&#xa;after extract_to_postgres"),
    ("transform_orders",        "Waits for customers&#xa;&amp; products transforms"),
    ("truncate_raw",            "Clears raw tables&#xa;&amp; raw MinIO files"),
]
task_x_start = af_x + af_w + 30
task_avail = CW - (task_x_start - ML) - 40
task_gap = 15
task_w = (task_avail - task_gap * (len(tasks)-1)) // len(tasks)
task_h = L4_H - HDR - 30
task_y = L4_Y + HDR + 15

task_ids = []
for k, (tname, tbody) in enumerate(tasks):
    tx = task_x_start + k * (task_w + task_gap)
    t_id2 = nid()
    cells.append(rect(t_id2, "1", "", box_bg(col), tx, task_y, task_w, task_h))
    th_id = nid()
    cells.append(rect(th_id, "1", tname, box_hdr(col),
                      tx, task_y, task_w, BOX_HDR))
    tb_id = nid()
    cells.append(rect(tb_id, "1", tbody,
                      "text;html=1;align=center;verticalAlign=middle;"
                      "strokeColor=none;fillColor=none;fontSize=9;",
                      tx, task_y+BOX_HDR, task_w, task_h-BOX_HDR))
    task_ids.append(t_id2)

# Arrows: sidebar → task1, then task→task
arr_af_t1 = nid()
cells.append(edge(arr_af_t1, "1", af_id, task_ids[0], arrow_style(col)))
for k in range(len(task_ids)-1):
    arr_id = nid()
    cells.append(edge(arr_id, "1", task_ids[k], task_ids[k+1], arrow_style(col)))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — TRANSFORMATION
# ─────────────────────────────────────────────────────────────────────────────
col = C["trans"]
l5_bg = nid()
cells.append(rect(l5_bg, "1", "", lane_bg(col), ML, L5_Y, CW, L5_H))
l5_hdr = nid()
cells.append(rect(l5_hdr, "1", "LAYER 5 — TRANSFORMATION", lane_hdr(col), ML, L5_Y, CW, HDR))

col5_data = [
    ("Python Transform Scripts",
     "transform_customers.py&#xa;transform_products.py&#xa;"
     "transform_orders.py&#xa;Via db_utils.py (shared)"),
    ("PySpark Notebooks&#xa;(Distributed transform prototyping)",
     "orders_transform_pyspark&#xa;(customers / products)"),
    ("JupyterLab Notebooks",
     "01_raw_exploration.ipynb&#xa;customers_transform.ipynb&#xa;"
     "products_transform.ipynb&#xa;orders_transform_pyspark.ipynb"),
]
col5_gap = 20
col5_w = (CW - 80 - col5_gap * 2) // 3
col5_h = L5_H - HDR - 30
col5_y = L5_Y + HDR + 15

for k, (chdr, cbody) in enumerate(col5_data):
    cx5 = ML + 40 + k * (col5_w + col5_gap)
    c5_id = nid()
    cells.append(rect(c5_id, "1", "", box_bg(col), cx5, col5_y, col5_w, col5_h))
    ch_id = nid()
    cells.append(rect(ch_id, "1", chdr, box_hdr(col), cx5, col5_y, col5_w, BOX_HDR))
    cb_id = nid()
    cells.append(rect(cb_id, "1", cbody,
                      "text;html=1;align=center;verticalAlign=middle;"
                      "strokeColor=none;fillColor=none;fontSize=10;",
                      cx5, col5_y+BOX_HDR, col5_w, col5_h-BOX_HDR))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6 — SERVING
# ─────────────────────────────────────────────────────────────────────────────
col = C["serve"]
l6_bg = nid()
cells.append(rect(l6_bg, "1", "", lane_bg(col), ML, L6_Y, CW, L6_H))
l6_hdr = nid()
cells.append(rect(l6_hdr, "1", "LAYER 6 — SERVING", lane_hdr(col), ML, L6_Y, CW, HDR))

half6 = (CW - 80) // 2 - 10
r6_y = L6_Y + HDR + 15
r6_h = L6_H - HDR - 30

# PostgreSQL staging
pg6_id = nid()
cells.append(rect(pg6_id, "1", "", box_bg(col), ML+40, r6_y, half6, r6_h))
pg6h_id = nid()
cells.append(rect(pg6h_id, "1", "PostgreSQL 15 — staging schema", box_hdr(col),
                  ML+40, r6_y, half6, BOX_HDR))
pg6b_id = nid()
cells.append(rect(pg6b_id, "1",
                  "staging.customers (200+ customer_id)&#xa;"
                  "staging.orders (STG product_id)&#xa;"
                  "staging.products (STG: customers, products)&#xa;"
                  "Ready for BI / analytics / warehouse",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=10;",
                  ML+40, r6_y+BOX_HDR, half6, r6_h-BOX_HDR))

# MongoDB Atlas
mg6_x = ML + 40 + half6 + 20
mg6_id = nid()
cells.append(rect(mg6_id, "1", "", box_bg(col), mg6_x, r6_y, half6, r6_h))
mg6h_id = nid()
cells.append(rect(mg6h_id, "1", "MongoDB Atlas — Document Store", box_hdr(col),
                  mg6_x, r6_y, half6, BOX_HDR))
mg6b_id = nid()
cells.append(rect(mg6b_id, "1",
                  "mandera_db database&#xa;"
                  "customers / orders / products collections&#xa;"
                  "Logging + change tracking&#xa;"
                  "Source of truth for raw documents",
                  "text;html=1;align=center;verticalAlign=middle;"
                  "strokeColor=none;fillColor=none;fontSize=10;",
                  mg6_x, r6_y+BOX_HDR, half6, r6_h-BOX_HDR))

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 7 — INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────────────────────
col = C["infra"]
l7_bg = nid()
cells.append(rect(l7_bg, "1", "", lane_bg(col), ML, L7_Y, CW, L7_H))
l7_hdr = nid()
cells.append(rect(l7_hdr, "1", "LAYER 7 — INFRASTRUCTURE  |  Docker Compose — 8 services",
                  lane_hdr(col), ML, L7_Y, CW, HDR))

services = ["postgres","minio","pgadmin","jupyter",
            "airflow-init","airflow-web","airflow-sched","db-init"]
svc_gap = 15
svc_w = (CW - 80 - svc_gap * (len(services)-1)) // len(services)
svc_h = L7_H - HDR - 30
svc_y = L7_Y + HDR + 15

for k, svc in enumerate(services):
    sx7 = ML + 40 + k * (svc_w + svc_gap)
    sv_id = nid()
    cells.append(rect(sv_id, "1", svc, svc_box(col), sx7, svc_y, svc_w, svc_h))

# ─────────────────────────────────────────────────────────────────────────────
# VERTICAL INTER-LAYER ARROWS
# ─────────────────────────────────────────────────────────────────────────────
layer_pairs = [
    (l1_bg, l2_bg, C["cicd"]),
    (l2_bg, l3_bg, C["gen"]),
    (l3_bg, l4_bg, C["raw"]),
    (l4_bg, l5_bg, C["orch"]),
    (l5_bg, l6_bg, C["trans"]),
    (l6_bg, l7_bg, C["serve"]),
]
for src, tgt, c in layer_pairs:
    arr_id = nid()
    cells.append(edge(arr_id, "1", src, tgt, varrow_style(c)))

# ─────────────────────────────────────────────────────────────────────────────
# ASSEMBLE XML
# ─────────────────────────────────────────────────────────────────────────────
xml = f'''\
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2026-05-07T00:00:00.000Z"
        agent="Claude Code" version="21.0.0" type="device">
  <diagram id="mandera-pipeline" name="MANDERA_ANALYTICS Pipeline">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10"
                  guides="1" tooltips="1" connect="1" arrows="1"
                  fold="1" page="1" pageScale="1"
                  pageWidth="{TW}" pageHeight="{TOTAL_H}"
                  math="0" shadow="1">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
{"".join("        " + c for c in cells)}      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''

out = pathlib.Path(__file__).parent / "architecture.drawio"
out.write_text(xml, encoding="utf-8")
print(f"Saved → {out}  ({out.stat().st_size // 1024} KB)")
