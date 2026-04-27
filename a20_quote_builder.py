import streamlit as st
import anthropic
import time
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ─────────────────────────────────────────────
# Fonts
# ─────────────────────────────────────────────
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

# ─────────────────────────────────────────────
# Anthropic init
# ─────────────────────────────────────────────
def get_client():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="A20 Quote Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS — DM Serif + DM Mono, #f5f7ff base, #1a2040 ink
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f5f7ff !important;
    color: #1a2040 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1.5px solid #dde3f5 !important;
}
[data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSidebar"] .st-emotion-cache-16txtl3 { padding: 2rem 1rem !important; }

/* Headers */
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; color: #1a2040 !important; }
.stMarkdown p, .stText { font-family: 'DM Sans', sans-serif !important; }

/* Inputs */
input, select, textarea { font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border: 1.5px solid #dde3f5 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: #1a2040 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #4f5fb8 !important;
    box-shadow: 0 0 0 3px rgba(79,95,184,0.12) !important;
}

/* Slider */
[data-testid="stSlider"] .st-emotion-cache-1dp5vir { background: #1a2040 !important; }

/* Buttons */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #1a2040 !important;
    color: #ffffff !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover { background: #2c3460 !important; }
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: #1a2040 !important;
    border: 1.5px solid #1a2040 !important;
}
.stButton > button[kind="secondary"]:hover { background: #f5f7ff !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: #1a2040 !important;
    border: 1.5px solid #1a2040 !important;
    font-weight: 500 !important;
}
[data-testid="stDownloadButton"] > button:hover { background: #f5f7ff !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 0.5px solid #dde3f5 !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
}
[data-testid="stMetricLabel"] { font-family: 'DM Mono', monospace !important; font-size: 11px !important; color: #6b7299 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
[data-testid="stMetricValue"] { font-family: 'DM Serif Display', serif !important; font-size: 28px !important; color: #1a2040 !important; }

/* Info / warning boxes */
[data-testid="stInfo"], [data-testid="stWarning"], [data-testid="stSuccess"] {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Expander */
[data-testid="stExpander"] {
    border: 0.5px solid #dde3f5 !important;
    border-radius: 10px !important;
    background: #ffffff !important;
}

/* Divider */
hr { border-color: #dde3f5 !important; }

/* Code / mono */
code { font-family: 'DM Mono', monospace !important; font-size: 12px !important; }

/* AI block */
.ai-block {
    background: linear-gradient(180deg, #e8edff 0%, #f5f7ff 100%);
    border: 1px solid #b8c5ff;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 8px 0 14px;
}
.ai-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #4f5fb8;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.ai-text { font-size: 14px; color: #1a2040; line-height: 1.6; }

/* Section title */
.sec-title {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #6b7299;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}

/* Badge */
.badge-new { background: #e0e8ff; color: #2c3caa; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-family: 'DM Mono', monospace; }
.badge-follow { background: #fff3cd; color: #7a5500; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-family: 'DM Mono', monospace; }
.badge-quoted { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-family: 'DM Mono', monospace; }
.badge-won { background: #1a2040; color: #ffffff; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-family: 'DM Mono', monospace; }

/* Lead card */
.lead-card {
    background: #ffffff;
    border: 0.5px solid #dde3f5;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: box-shadow 0.15s;
}
.lead-card:hover { box-shadow: 0 4px 16px rgba(26,32,64,0.08); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Data — Products, GPUs, Brands
# ─────────────────────────────────────────────
CATEGORIES = [
    {"id": "server",      "label": "A20 伺服器",    "sub": "整機 · OEM 配置",     "rate": 0.07, "lead_mode": "weeks"},
    {"id": "workstation", "label": "DGX · 工作站",  "sub": "桌邊型 AI 設備",      "rate": 0.05, "lead_mode": "weeks"},
    {"id": "cloud",       "label": "GPU2.COM 雲端", "sub": "K8s 即開即用",        "rate": 0.15, "lead_mode": "instant"},
    {"id": "vast",        "label": "Vast.AI 託管",  "sub": "轉租 + A20 維運",     "rate": 0.25, "lead_mode": "hours"},
]

GPUS = [
    {"id": "rtx5090",  "label": "RTX 5090",      "vram": 32,  "tier": "消費級",   "price": 2999,  "tflops": 104,  "brands": ["supermicro","gigabyte","asus"],                       "lead": [2,4],  "public": True},
    {"id": "pro6000",  "label": "RTX Pro 6000",  "vram": 96,  "tier": "工作站",   "price": 8500,  "tflops": 125,  "brands": ["supermicro","gigabyte","asus","dell","hpe"],            "lead": [3,6],  "public": True},
    {"id": "h100",     "label": "H100 SXM",      "vram": 80,  "tier": "訓練",     "price": 28000, "tflops": 989,  "brands": ["supermicro","gigabyte","asus","wiwynn","quanta"],       "lead": [8,12], "public": True},
    {"id": "h200",     "label": "H200",           "vram": 141, "tier": "推論",     "price": 32000, "tflops": 989,  "brands": ["supermicro","gigabyte","wiwynn"],                       "lead": [10,14],"public": True},
    {"id": "b200",     "label": "B200",           "vram": 192, "tier": "旗艦",     "price": 42000, "tflops": 2250, "brands": ["supermicro","wiwynn","quanta"],                         "lead": [16,24],"public": False},
]

BRANDS = [
    {"id": "supermicro", "label": "Supermicro · 美超微",       "mod": 0},
    {"id": "gigabyte",   "label": "技嘉 GIGABYTE · G/H 系列",  "mod": 0},
    {"id": "asus",       "label": "華碩 ASUS · ESC 系列",       "mod": 1},
    {"id": "wiwynn",     "label": "緯穎 Wiwynn · 雲端代工",     "mod": 2},
    {"id": "quanta",     "label": "廣達 Quanta QCT",            "mod": 2},
    {"id": "dell",       "label": "Dell PowerEdge",             "mod": 1},
    {"id": "hpe",        "label": "HPE ProLiant",               "mod": 1},
]

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "cat_id":    "server",
        "gpu_id":    "h100",
        "brand_id":  None,
        "quantity":  8,
        "use_case":  "",
        "ai_advice": "",
        "leads":     [
            {"id":"L001","name":"陳俊宏","company":"奧義智慧","cat":"Vast.AI 託管","gpu":"H200×4","price":"USD 12K/月","status":"follow","use_case":"推論服務上線","time":"3 小時前"},
            {"id":"L002","name":"Sarah Chen","company":"Stealth AI","cat":"A20 伺服器","gpu":"B200×16","price":"需報價","status":"follow","use_case":"大規模訓練","time":"昨天"},
            {"id":"L003","name":"林雅婷","company":"台大資工實驗室","cat":"DGX 工作站","gpu":"DGX Spark×2","price":"USD 9.4K","status":"quoted","use_case":"實驗室桌邊配置","time":"3 天前"},
            {"id":"L004","name":"張承恩","company":"遊戲新創 K","cat":"GPU2.COM 雲端","gpu":"5090×8","price":"USD 4.6K/月","status":"won","use_case":"Diffusion 訓練","time":"1 週前"},
        ],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def get_gpu(gid): return next((g for g in GPUS if g["id"] == gid), GPUS[2])
def get_cat(cid): return next((c for c in CATEGORIES if c["id"] == cid), CATEGORIES[0])
def get_brand(bid): return next((b for b in BRANDS if b["id"] == bid), None) if bid else None

def calc_quote(cat_id, gpu_id, brand_id, qty):
    gpu = get_gpu(gpu_id)
    cat = get_cat(cat_id)
    brand = get_brand(brand_id)
    hw = gpu["price"] * qty
    svc = round(hw * cat["rate"])
    total = hw + svc
    mod = brand["mod"] if brand else 0
    qty_add = 0 if qty <= 4 else 4 if qty <= 16 else 8
    if cat["lead_mode"] == "instant":
        lead_text = "即日開通"
    elif cat["lead_mode"] == "hours":
        lead_text = "24–72 小時"
    else:
        mn = gpu["lead"][0] + mod
        mx = gpu["lead"][1] + mod + qty_add
        lead_text = f"{mn}–{mx} 週"
    block = not gpu["public"] or qty > 32
    return {
        "hw": hw, "svc": svc, "total": total,
        "lead_text": lead_text, "block": block,
    }

def fmt_usd(n): return f"USD {n:,.0f}"

def get_ai_advice(cat_id, gpu_id, brand_id, qty, use_case):
    cat = get_cat(cat_id)
    gpu = get_gpu(gpu_id)
    brand = get_brand(brand_id)
    q = calc_quote(cat_id, gpu_id, brand_id, qty)
    brand_str = brand["label"] if brand else "A20 推薦供應"
    prompt = f"""你是 A20 Research Lab 的 GPU 採購顧問。根據以下配置與客戶需求，給出 3–5 點具體建議，用繁體中文，語氣專業簡潔，不要使用 markdown 符號，每點換行，最後一行寫交期與總價提醒。

配置：{cat['label']} / {gpu['label']} × {qty} / 廠商：{brand_str}
估價：{fmt_usd(q['total'])}（硬體 {fmt_usd(q['hw'])} + 服務包 {fmt_usd(q['svc'])}）
交期：{q['lead_text']}
客戶用途：{use_case if use_case else '未填寫'}

請給出針對此配置的採購建議。"""
    client = get_client()
    result = []
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            result.append(text)
            yield "".join(result)

# ─────────────────────────────────────────────
# PDF builder
# ─────────────────────────────────────────────
def build_pdf(cat_id, gpu_id, brand_id, qty, use_case, contact_name, contact_company, ai_text):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=20*mm, rightMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)
    cat = get_cat(cat_id)
    gpu = get_gpu(gpu_id)
    brand = get_brand(brand_id)
    q = calc_quote(cat_id, gpu_id, brand_id, qty)
    brand_str = brand["label"] if brand else "由 A20 推薦"

    S = {
        "h1":    ParagraphStyle("h1",    fontName="STSong-Light", fontSize=22, leading=28, textColor=colors.HexColor("#1a2040"), spaceAfter=4),
        "h2":    ParagraphStyle("h2",    fontName="STSong-Light", fontSize=14, leading=20, textColor=colors.HexColor("#1a2040"), spaceBefore=14, spaceAfter=6),
        "body":  ParagraphStyle("body",  fontName="STSong-Light", fontSize=11, leading=17, textColor=colors.HexColor("#1a2040")),
        "small": ParagraphStyle("small", fontName="STSong-Light", fontSize=9,  leading=14, textColor=colors.HexColor("#6b7299")),
        "mono":  ParagraphStyle("mono",  fontName="STSong-Light", fontSize=9,  leading=14, textColor=colors.HexColor("#4f5fb8")),
        "price": ParagraphStyle("price", fontName="STSong-Light", fontSize=28, leading=34, textColor=colors.HexColor("#1a2040")),
    }

    def hr(): return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dde3f5"), spaceAfter=10, spaceBefore=10)

    def table(data, col_widths, row_colors=None):
        t = Table(data, colWidths=col_widths)
        style_cmds = [
            ("FONTNAME", (0,0), (-1,-1), "STSong-Light"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#1a2040")),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#f5f7ff"), colors.white]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#dde3f5")),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("FONTNAME", (0,0), (-1,0), "STSong-Light"),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#6b7299")),
            ("FONTSIZE", (0,0), (-1,0), 9),
        ]
        t.setStyle(TableStyle(style_cmds))
        return t

    story = []

    # Header
    story.append(Paragraph("A20 Research Lab", S["mono"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("指引估價報告", S["h1"]))
    story.append(Paragraph(f"製作日期：{time.strftime('%Y-%m-%d')}　　有效期：7 天", S["small"]))
    story.append(Spacer(1, 6))
    story.append(hr())

    # Client info
    if contact_name or contact_company:
        story.append(Paragraph("客戶資訊", S["h2"]))
        rows = [["姓名", contact_name or "—"], ["公司", contact_company or "—"]]
        if use_case: rows.append(["用途", use_case])
        story.append(table(rows, [40*mm, 130*mm]))
        story.append(Spacer(1, 8))
        story.append(hr())

    # Config
    story.append(Paragraph("配置摘要", S["h2"]))
    config_rows = [
        ["方案類別", cat["label"]],
        ["GPU 型號", gpu["label"]],
        ["VRAM", f"{gpu['vram']} GB"],
        ["廠商品牌", brand_str],
        ["數量", f"{qty} 卡"],
        ["交期估算", q["lead_text"]],
    ]
    story.append(table(config_rows, [50*mm, 120*mm]))
    story.append(Spacer(1, 12))
    story.append(hr())

    # Price
    story.append(Paragraph("費用明細", S["h2"]))
    if q["block"]:
        story.append(Paragraph("此配置需客製化報價，請聯繫業務。", S["body"]))
    else:
        price_rows = [
            ["項目", "金額（USD）"],
            ["硬體費用", f"${q['hw']:,.0f}"],
            ["A20 服務包", f"${q['svc']:,.0f}"],
            ["合計（指引價）", f"${q['total']:,.0f}"],
        ]
        t = table(price_rows, [100*mm, 70*mm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "STSong-Light"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("FONTNAME", (0,-1), (-1,-1), "STSong-Light"),
            ("FONTSIZE", (0,-1), (-1,-1), 13),
            ("TEXTCOLOR", (0,-1), (-1,-1), colors.HexColor("#1a2040")),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#f5f7ff"), colors.white, colors.HexColor("#e8edff")]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#dde3f5")),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(t)
    story.append(Spacer(1, 8))
    story.append(hr())

    # AI advice
    if ai_text and ai_text.strip():
        story.append(Paragraph("A20 AI 配置建議", S["h2"]))
        story.append(Paragraph(ai_text.replace("\n", "<br/>"), S["body"]))
        story.append(Spacer(1, 8))
        story.append(hr())

    # Footer
    story.append(Spacer(1, 8))
    story.append(Paragraph("本報告為指引估價，非正式報價。最終價格以業務出具之正式報價單為準。", S["small"]))
    story.append(Paragraph("A20 Research Lab　|　sales@a20.ai　|　honghutech.com", S["small"]))

    doc.build(story)
    return buf.getvalue()

# ─────────────────────────────────────────────
# Sidebar nav
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='margin-bottom: 6px;'>
      <span style='font-family: "DM Serif Display", serif; font-size: 22px; color: #1a2040;'>A20 Quote</span>
    </div>
    <div style='font-family: "DM Mono", monospace; font-size: 11px; color: #6b7299; margin-bottom: 24px;'>GPU · 伺服器 · 雲端算力</div>
    """, unsafe_allow_html=True)

    tab = st.radio(
        "導航",
        ["📊  配置與報價", "🤖  AI 需求顧問", "📥  Lead 收件匣", "📈  業績儀表板"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
    <div style='font-family: "DM Mono", monospace; font-size: 10px; color: #b0b8d8; line-height: 1.8;'>
    A20 Research Lab<br>
    v0.1 · prototype<br>
    sales@a20.ai
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 1 — 配置與報價
# ─────────────────────────────────────────────
if "配置與報價" in tab:
    st.markdown("# 配置與報價")
    st.markdown('<p style="font-family: \'DM Mono\', monospace; font-size: 12px; color: #6b7299; margin-top: -12px; margin-bottom: 24px;">A20 · GPU2.COM · DGX · Vast.AI</p>', unsafe_allow_html=True)

    col_form, col_summary = st.columns([3, 2], gap="large")

    with col_form:
        # Step 1
        st.markdown('<div class="sec-title">01 · 方案類別</div>', unsafe_allow_html=True)
        cat_labels = [f"{c['label']}  —  {c['sub']}" for c in CATEGORIES]
        cat_idx = next(i for i, c in enumerate(CATEGORIES) if c["id"] == st.session_state.cat_id)
        selected_cat_label = st.selectbox("方案", cat_labels, index=cat_idx, label_visibility="collapsed")
        st.session_state.cat_id = CATEGORIES[cat_labels.index(selected_cat_label)]["id"]

        # Step 2
        st.markdown('<div class="sec-title" style="margin-top: 20px;">02 · GPU 卡型</div>', unsafe_allow_html=True)
        gpu_labels = [f"{g['label']}  ·  {g['vram']}GB  ·  {g['tier']}" + (" ⟶ 需報價" if not g["public"] else "") for g in GPUS]
        gpu_idx = next(i for i, g in enumerate(GPUS) if g["id"] == st.session_state.gpu_id)
        selected_gpu_label = st.selectbox("GPU", gpu_labels, index=gpu_idx, label_visibility="collapsed")
        new_gpu_id = GPUS[gpu_labels.index(selected_gpu_label)]["id"]
        if new_gpu_id != st.session_state.gpu_id:
            st.session_state.gpu_id = new_gpu_id
            st.session_state.brand_id = None

        # Step 3
        st.markdown('<div class="sec-title" style="margin-top: 20px;">03 · 廠商品牌</div>', unsafe_allow_html=True)
        gpu = get_gpu(st.session_state.gpu_id)
        avail_brands = [b for b in BRANDS if b["id"] in gpu["brands"]]
        brand_options = ["由 A20 推薦最佳供應"] + [b["label"] for b in avail_brands]
        cur_brand_idx = 0
        if st.session_state.brand_id:
            b_labels = [b["label"] for b in avail_brands]
            if get_brand(st.session_state.brand_id) and get_brand(st.session_state.brand_id)["label"] in b_labels:
                cur_brand_idx = b_labels.index(get_brand(st.session_state.brand_id)["label"]) + 1
        selected_brand = st.selectbox("廠商", brand_options, index=cur_brand_idx, label_visibility="collapsed")
        if selected_brand == "由 A20 推薦最佳供應":
            st.session_state.brand_id = None
        else:
            matched = next((b for b in avail_brands if b["label"] == selected_brand), None)
            st.session_state.brand_id = matched["id"] if matched else None

        # Step 4
        cat = get_cat(st.session_state.cat_id)
        unit = "卡" if cat["id"] in ["cloud", "vast"] else "台"
        st.markdown(f'<div class="sec-title" style="margin-top: 20px;">04 · 數量（{unit}）</div>', unsafe_allow_html=True)
        st.session_state.quantity = st.slider(
            "數量", min_value=1, max_value=64,
            value=st.session_state.quantity, label_visibility="collapsed"
        )

        # Step 5 — use case
        st.markdown('<div class="sec-title" style="margin-top: 20px;">05 · 用途描述（選填）</div>', unsafe_allow_html=True)
        st.session_state.use_case = st.text_area(
            "用途", value=st.session_state.use_case,
            placeholder="例：訓練 70B 多模態模型，預計 3 個月內擴張到 32 卡規模",
            height=80, label_visibility="collapsed"
        )

    with col_summary:
        q = calc_quote(st.session_state.cat_id, st.session_state.gpu_id, st.session_state.brand_id, st.session_state.quantity)

        st.markdown('<div class="sec-title">即時估價</div>', unsafe_allow_html=True)

        if q["block"]:
            st.warning("⟶ 此配置需客製化報價，請洽業務")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("合計", fmt_usd(q["total"]))
            m2.metric("硬體", fmt_usd(q["hw"]))
            m3.metric("服務包", fmt_usd(q["svc"]))

        st.metric("交期估算", q["lead_text"])

        st.markdown("---")

        # AI Advice
        st.markdown('<div class="sec-title">AI 配置建議</div>', unsafe_allow_html=True)
        if st.button("⟶ 產生 AI 建議", type="primary", use_container_width=True):
            advice_placeholder = st.empty()
            full_text = ""
            for chunk in get_ai_advice(
                st.session_state.cat_id, st.session_state.gpu_id,
                st.session_state.brand_id, st.session_state.quantity,
                st.session_state.use_case
            ):
                full_text = chunk
                advice_placeholder.markdown(
                    f'<div class="ai-block"><div class="ai-tag">CLAUDE AI · 配置建議</div><div class="ai-text">{full_text.replace(chr(10), "<br/>")}</div></div>',
                    unsafe_allow_html=True
                )
            st.session_state.ai_advice = full_text
        elif st.session_state.ai_advice:
            st.markdown(
                f'<div class="ai-block"><div class="ai-tag">CLAUDE AI · 配置建議</div><div class="ai-text">{st.session_state.ai_advice.replace(chr(10), "<br/>")}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # Contact form + PDF
        st.markdown('<div class="sec-title">聯絡資訊</div>', unsafe_allow_html=True)
        contact_name = st.text_input("姓名", placeholder="王小明")
        contact_company = st.text_input("公司", placeholder="長日智能")
        contact_email = st.text_input("Email", placeholder="you@company.com")
        contact_phone = st.text_input("電話（選填）", placeholder="+886 9XX-XXX-XXX")

        col_pdf, col_lead = st.columns(2)

        with col_pdf:
            if st.button("📄 下載 PDF", use_container_width=True):
                pdf = build_pdf(
                    st.session_state.cat_id, st.session_state.gpu_id,
                    st.session_state.brand_id, st.session_state.quantity,
                    st.session_state.use_case, contact_name, contact_company,
                    st.session_state.ai_advice
                )
                st.download_button(
                    "⬇ 下載報價單",
                    data=pdf,
                    file_name=f"A20_指引估價_{contact_name or 'quote'}_{time.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        with col_lead:
            if st.button("📨 請業務聯繫", type="primary", use_container_width=True):
                if not contact_name or not contact_email:
                    st.error("請填入姓名與 Email")
                else:
                    gpu = get_gpu(st.session_state.gpu_id)
                    cat = get_cat(st.session_state.cat_id)
                    new_lead = {
                        "id": f"L{len(st.session_state.leads)+1:03d}",
                        "name": contact_name,
                        "company": contact_company or "—",
                        "cat": cat["label"],
                        "gpu": f"{gpu['label']}×{st.session_state.quantity}",
                        "price": fmt_usd(q["total"]) if not q["block"] else "需報價",
                        "status": "new",
                        "use_case": st.session_state.use_case or "未填寫",
                        "time": "剛剛",
                        "email": contact_email,
                        "phone": contact_phone,
                    }
                    st.session_state.leads.insert(0, new_lead)
                    st.success(f"✅ Lead 已送出！業務 24 小時內聯繫 {contact_email}")

# ─────────────────────────────────────────────
# TAB 2 — AI 需求顧問
# ─────────────────────────────────────────────
elif "AI 需求顧問" in tab:
    st.markdown("# AI 需求顧問")
    st.markdown('<p style="font-family: \'DM Mono\', monospace; font-size: 12px; color: #6b7299; margin-top: -12px; margin-bottom: 24px;">用自然語言描述需求，AI 推薦最適合的 3 種配置</p>', unsafe_allow_html=True)

    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []

    user_input = st.text_area(
        "描述你的需求",
        placeholder="例：我要訓練一個 70B 參數的多模態模型，預算大概 200–300 萬台幣，希望 3 個月內可以用，未來可能擴到 32 卡",
        height=100,
    )

    if st.button("⟶ 送出需求，讓 AI 推薦配置", type="primary"):
        if user_input.strip():
            prompt = f"""你是 A20 Research Lab 的 GPU 採購顧問。根據客戶需求，推薦 3 種配置方案，格式如下：

方案一：[方案名稱]
- GPU：[型號 × 數量]
- 廠商：[推薦廠商]
- 預估總價：[USD 金額]
- 適合原因：[2 句話]

方案二：...（預算較低的替代方案）
方案三：...（未來擴充考量）

最後一段：整體建議，50 字以內。

客戶需求：{user_input}

請用繁體中文回覆，不要使用 markdown 符號。"""

            st.session_state.ai_chat = [{"role": "user", "content": user_input}]
            placeholder = st.empty()
            result = []
            client = get_client()
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    result.append(text)
                    txt = "".join(result)
                    placeholder.markdown(
                        f'<div class="ai-block"><div class="ai-tag">CLAUDE AI · 需求分析</div><div class="ai-text">{txt.replace(chr(10), "<br/>")}</div></div>',
                        unsafe_allow_html=True
                    )
            st.session_state.ai_chat.append({"role": "assistant", "content": "".join(result)})
        else:
            st.warning("請填入需求描述")

    if st.session_state.ai_chat and len(st.session_state.ai_chat) >= 2:
        response = st.session_state.ai_chat[-1]["content"]
        st.markdown(
            f'<div class="ai-block"><div class="ai-tag">CLAUDE AI · 需求分析</div><div class="ai-text">{response.replace(chr(10), "<br/>")}</div></div>',
            unsafe_allow_html=True
        )
        st.info("想直接下載這個建議的 PDF？切換到「配置與報價」頁面完成配置後下載。")

# ─────────────────────────────────────────────
# TAB 3 — Lead 收件匣
# ─────────────────────────────────────────────
elif "Lead 收件匣" in tab:
    st.markdown("# Lead 收件匣")
    st.markdown('<p style="font-family: \'DM Mono\', monospace; font-size: 12px; color: #6b7299; margin-top: -12px; margin-bottom: 24px;">業務後台 · 僅限內部查看</p>', unsafe_allow_html=True)

    leads = st.session_state.leads
    total = len(leads)
    new_c = sum(1 for l in leads if l["status"] == "new")
    follow_c = sum(1 for l in leads if l["status"] == "follow")
    quoted_c = sum(1 for l in leads if l["status"] == "quoted")
    won_c = sum(1 for l in leads if l["status"] == "won")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("本月新進", total)
    m2.metric("新進", new_c)
    m3.metric("跟進中", follow_c)
    m4.metric("已報價", quoted_c)
    m5.metric("成交", won_c)

    st.markdown("---")

    status_filter = st.radio("篩選", ["全部", "新進", "跟進中", "已報價", "成交"],
                              horizontal=True, label_visibility="collapsed")
    status_map = {"全部": None, "新進": "new", "跟進中": "follow", "已報價": "quoted", "成交": "won"}
    filtered = [l for l in leads if status_map[status_filter] is None or l["status"] == status_map[status_filter]]

    badge_map = {
        "new":    '<span class="badge-new">新進</span>',
        "follow": '<span class="badge-follow">跟進中</span>',
        "quoted": '<span class="badge-quoted">已報價</span>',
        "won":    '<span class="badge-won">成交</span>',
    }

    for lead in filtered:
        with st.expander(f"{lead['name']} · {lead['company']}  —  {lead['gpu']}  ·  {lead['time']}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.markdown(f"**方案** {lead['cat']}")
                st.markdown(f"**GPU** {lead['gpu']}")
                st.markdown(f"**用途** {lead['use_case']}")
            with c2:
                st.markdown(f"**指引價** {lead['price']}")
                st.markdown(f"**Email** {lead.get('email', '—')}")
                st.markdown(f"**電話** {lead.get('phone', '—')}")
            with c3:
                st.markdown(badge_map.get(lead["status"], ""), unsafe_allow_html=True)
                new_status = st.selectbox(
                    "更新狀態",
                    ["new", "follow", "quoted", "won"],
                    index=["new", "follow", "quoted", "won"].index(lead["status"]),
                    key=f"status_{lead['id']}",
                    label_visibility="collapsed"
                )
                if new_status != lead["status"]:
                    lead["status"] = new_status
                    st.rerun()

# ─────────────────────────────────────────────
# TAB 4 — 業績儀表板
# ─────────────────────────────────────────────
elif "業績儀表板" in tab:
    st.markdown("# 業績儀表板")
    st.markdown('<p style="font-family: \'DM Mono\', monospace; font-size: 12px; color: #6b7299; margin-top: -12px; margin-bottom: 24px;">本月概覽</p>', unsafe_allow_html=True)

    leads = st.session_state.leads
    won_leads = [l for l in leads if l["status"] == "won"]
    follow_leads = [l for l in leads if l["status"] == "follow"]
    conv_rate = len(won_leads) / len(leads) * 100 if leads else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("總 Lead 數", len(leads))
    m2.metric("成交數", len(won_leads))
    m3.metric("轉換率", f"{conv_rate:.1f}%")
    m4.metric("跟進中", len(follow_leads))

    st.markdown("---")

    st.markdown('<div class="sec-title">方案分布</div>', unsafe_allow_html=True)
    cat_count = {}
    for l in leads:
        cat_count[l["cat"]] = cat_count.get(l["cat"], 0) + 1

    rows = [["方案", "Lead 數", "佔比"]]
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        pct = cnt / len(leads) * 100
        rows.append([cat, str(cnt), f"{pct:.0f}%"])

    col_tbl, col_tip = st.columns([2, 1])
    with col_tbl:
        st.table({
            "方案": [r[0] for r in rows[1:]],
            "Lead 數": [r[1] for r in rows[1:]],
            "佔比": [r[2] for r in rows[1:]],
        })
    with col_tip:
        st.markdown(
            '<div class="ai-block"><div class="ai-tag">本月洞察</div><div class="ai-text" style="font-size:13px;">A20 伺服器與雲端方案 Lead 佔大宗。B200 詢問量上升，建議業務準備客製報價模板。Vast.AI 轉換率低，可考慮加入 SLA 比較文件。</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown('<div class="sec-title">成交清單</div>', unsafe_allow_html=True)
    if won_leads:
        st.table({
            "客戶": [l["name"] for l in won_leads],
            "公司": [l["company"] for l in won_leads],
            "方案": [l["cat"] for l in won_leads],
            "金額": [l["price"] for l in won_leads],
        })
    else:
        st.info("本月尚無成交紀錄")
