import streamlit as st
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import io
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

IST = ZoneInfo('Asia/Kolkata')
import random
import json
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="ChaiFi – Billing", page_icon="☕", layout="wide")

# ── Menu ──────────────────────────────────────────────────────────────────────
MENU = {
    "🍵 Beverages": {
        "Spl Gud ki Chai (Cup)":             15,
        "Spl Gud ki Chai (Khulad)":          20,
        "Lemon / Green / Black Tea":         30,
        "Cold Coffee ⭐ Must Try":            70,
        "Spl Masala Banta Soda ⭐":          40,
        "Regular Lassi":                     50,
        "Mango Lassi":                       60,
        "Kesar Badam Lassi":                 70,
    },
    "🍽️ Food Items": {
        "Bun Maska":                         40,
        "Plain Maggi":                       50,
        "Veg Maggi":                         60,
        "Grilled Aaloo Stuffed Patties ⭐":  60,
        "Grilled Paneer Stuffed Patties ⭐": 70,
        "Butter Masala Sweet Corn (S)":      50,
        "Butter Masala Sweet Corn (L)":      70,
        "Kulcha Pizza 🆕":                  100,
    },
}

DISCOUNT_THRESHOLD = 150
DISCOUNT_PCT       = 10
SHEET_NAME         = "ChaiFi_Bills"
WORKSHEET_NAME     = "Bills"

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ═══════════════════════════════════════
   BASE — light cafe theme
═══════════════════════════════════════ */
* { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #faf8f4;
    color: #1a1208;
    font-family: 'Inter', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ═══════════════════════════════════════
   HERO HEADER
═══════════════════════════════════════ */
.hero {
    background: linear-gradient(135deg, #fff 0%, #fffbf4 50%, #fff8ec 100%);
    border-bottom: 1px solid #e8dcc8;
    padding: 1.6rem 3rem 1.4rem;
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; flex-wrap: wrap; position: relative; overflow: hidden;
    box-shadow: 0 2px 16px rgba(184,114,10,.07);
}
.hero::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 80% 50%, rgba(232,160,32,.06) 0%, transparent 60%);
    pointer-events: none;
}
.hero-eyebrow {
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.18em; color: #c8880e; margin-bottom: 4px;
}
.hero-title {
    font-family: 'Playfair Display', serif; font-size: 1.9rem;
    font-weight: 900; color: #1a1208; line-height: 1.1; letter-spacing: -0.01em;
}
.hero-title span { color: #c8880e; }
.hero-sub { font-size: 0.72rem; color: #a89070; margin-top: 4px; font-weight: 400; }
.hero-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* ═══════════════════════════════════════
   BADGES
═══════════════════════════════════════ */
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.03em;
}
.badge-green { background: #edfaed; border: 1px solid #4caf50; color: #2e7d32; }
.badge-red   { background: #fdecea; border: 1px solid #f44336; color: #c62828; }

/* ═══════════════════════════════════════
   MAIN CONTENT WRAPPER
═══════════════════════════════════════ */
.main-wrap { padding: 2rem 3rem 3rem; max-width: 1400px; margin: 0 auto; }

/* ═══════════════════════════════════════
   TABS
═══════════════════════════════════════ */
[data-testid="stTabs"] [role="tablist"] {
    background: #fff; border-radius: 14px; padding: 5px;
    border: 1px solid #e8dcc8; gap: 4px; margin-bottom: 0.5rem;
    box-shadow: 0 1px 6px rgba(184,114,10,.06);
}
button[data-baseweb="tab"] {
    background: transparent !important; color: #b8a080 !important;
    border-radius: 10px !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    padding: 0.55rem 1.3rem !important; transition: all 0.2s !important;
    border: none !important; letter-spacing: 0.02em;
}
button[data-baseweb="tab"]:hover { color: #c8880e !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #b8720a, #e8a020) !important;
    color: #fff !important; box-shadow: 0 2px 12px rgba(184,114,10,.3) !important;
}
[data-testid="stTabs"] [role="tabpanel"] { padding-top: 1.8rem; }

/* ═══════════════════════════════════════
   INPUTS
═══════════════════════════════════════ */
input, textarea, div[data-baseweb="input"] input {
    background: #fff !important; color: #1a1208 !important;
    border-color: #e0d4c0 !important; border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}
.stSelectbox > div > div {
    background: #fff !important; border-color: #e0d4c0 !important;
    border-radius: 10px !important; color: #1a1208 !important;
}
input[type="number"] {
    background: #fff !important; color: #1a1208 !important;
    border: 1px solid #e0d4c0 !important; border-radius: 10px !important;
}
label, .stSelectbox label, .stNumberInput label, .stTextInput label {
    color: #b8a080 !important; font-size: 0.68rem !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.09em;
}
[data-baseweb="popover"] { background: #fff !important; border: 1px solid #e0d4c0 !important; }
[role="option"] { background: #fff !important; color: #1a1208 !important; }
[role="option"]:hover { background: #fff8ec !important; }

/* ═══════════════════════════════════════
   BUTTONS
═══════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg, #9a5e08, #c8880e, #e8a020) !important;
    color: #fff !important; font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important; border: none !important;
    border-radius: 10px !important; padding: 0.58rem 1.3rem !important;
    font-size: 0.85rem !important; letter-spacing: 0.02em;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 12px rgba(184,114,10,.25) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(184,114,10,.4) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

.stDownloadButton > button {
    background: #fff !important; color: #c8880e !important;
    border: 1.5px solid #e0d4c0 !important; border-radius: 10px !important;
    font-weight: 600 !important; font-family: 'Inter', sans-serif !important;
    font-size: 0.83rem !important; transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: #c8880e !important; color: #fff !important; border-color: #c8880e !important;
}

/* ═══════════════════════════════════════
   DIVIDER & ALERTS
═══════════════════════════════════════ */
hr { border: none !important; border-top: 1px solid #e8dcc8 !important; margin: 1.2rem 0 !important; }
.stAlert { border-radius: 10px !important; font-family: 'Inter', sans-serif !important; }

/* ═══════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #faf8f4; }
::-webkit-scrollbar-thumb { background: #e0d4c0; border-radius: 2px; }

/* ═══════════════════════════════════════
   SECTION LABEL
═══════════════════════════════════════ */
.section-title {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.15em; color: #c8b090; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 8px;
}
.section-title::after { content: ''; flex: 1; height: 1px; background: #e8dcc8; }

/* ═══════════════════════════════════════
   ITEM PICKER BAR
═══════════════════════════════════════ */
.picker-bar {
    background: #fff; border: 1px solid #e8dcc8; border-radius: 16px;
    padding: 1rem 1.4rem; margin-bottom: 1.4rem;
    box-shadow: 0 1px 8px rgba(184,114,10,.05);
}
.picker-title {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: #c8b090; margin-bottom: 0.8rem;
}

/* ═══════════════════════════════════════
   CART ITEM ROW
═══════════════════════════════════════ */
.cart-row {
    background: #fff; border: 1px solid #e8dcc8; border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px; transition: border-color 0.15s;
}
.cart-row:hover { border-color: #e8a020; }

/* ═══════════════════════════════════════
   TOTALS STRIP
═══════════════════════════════════════ */
.totals-strip {
    background: #fff; border: 1px solid #e8dcc8; border-radius: 14px;
    padding: 1rem 1.3rem; margin-top: 0.8rem;
    box-shadow: 0 1px 6px rgba(184,114,10,.04);
}
.totals-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; font-size: 0.85rem; }
.totals-row.grand {
    border-top: 1px solid #e8dcc8; margin-top: 10px; padding-top: 12px;
    font-size: 1.1rem; font-weight: 700;
}
.totals-row .t-label { color: #b8a080; }
.totals-row .t-val   { color: #1a1208; }
.nudge {
    background: #fff8ec; border: 1.5px dashed #e8a020; border-radius: 10px;
    padding: 10px 14px; font-size: 0.78rem; color: #c8880e;
    margin-top: 10px; text-align: center; font-weight: 500;
}

/* ═══════════════════════════════════════
   BILL RECEIPT
═══════════════════════════════════════ */
.bill-receipt {
    background: #fefcf5; border-radius: 14px; padding: 24px 28px;
    border: 1px solid #e8d8a0; box-shadow: 0 4px 20px rgba(184,114,10,.1);
    font-family: 'JetBrains Mono', monospace; color: #1a1000;
    position: relative; overflow: hidden;
}
.bill-receipt::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #9a5e08, #e8a020, #f5c842, #e8a020, #9a5e08);
}
.bill-receipt pre {
    margin: 0; font-size: 0.75rem; line-height: 1.85;
    background: transparent; color: #1a1000;
    white-space: pre; font-family: 'JetBrains Mono', monospace;
}

/* ═══════════════════════════════════════
   KPI CARDS
═══════════════════════════════════════ */
.kpi-card {
    background: #fff; border: 1px solid #e8dcc8; border-radius: 16px;
    padding: 1.3rem 1.5rem; transition: border-color 0.2s, transform 0.2s;
    position: relative; overflow: hidden;
    box-shadow: 0 1px 6px rgba(184,114,10,.05);
}
.kpi-card::before {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #b8720a, #e8a020); opacity: 0; transition: opacity 0.2s;
}
.kpi-card:hover { border-color: #e8a020; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(184,114,10,.12); }
.kpi-card:hover::before { opacity: 1; }
.kpi-label { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #c8b090; margin-bottom: 8px; }
.kpi-value { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 700; color: #b8720a; line-height: 1; margin-bottom: 4px; }
.kpi-sub   { font-size: 0.72rem; color: #b8a080; }

/* ═══════════════════════════════════════
   CHART CARDS
═══════════════════════════════════════ */
.chart-card { background: #fff; border: 1px solid #e8dcc8; border-radius: 16px; padding: 1.3rem 1.5rem; box-shadow: 0 1px 6px rgba(184,114,10,.04); }
.chart-card-title { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #c8b090; margin-bottom: 1rem; }
.bar-row   { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.bar-name  { font-size: 0.73rem; color: #b8a080; width: 150px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; background: #f5f0e8; border-radius: 6px; height: 18px; overflow: hidden; border: 1px solid #e8dcc8; }
.bar-fill  { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #9a5e08, #e8a020); }
.bar-num   { font-size: 0.73rem; color: #1a1208; font-weight: 600; width: 58px; text-align: right; flex-shrink: 0; }

/* ═══════════════════════════════════════
   HISTORY CARDS
═══════════════════════════════════════ */
.history-card {
    background: #fff; border: 1px solid #e8dcc8;
    border-radius: 12px; padding: 14px 16px; margin-bottom: 8px;
    transition: border-color 0.15s, box-shadow 0.15s;
    box-shadow: 0 1px 4px rgba(184,114,10,.04);
}
.history-card:hover { border-color: #e8a020; box-shadow: 0 3px 12px rgba(184,114,10,.1); }
.history-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.history-bill { font-size: 0.8rem; font-weight: 700; color: #b8720a; font-family: 'JetBrains Mono', monospace; }
.history-time { font-size: 0.7rem; color: #c8b090; }
.history-items { font-size: 0.76rem; color: #907060; margin-bottom: 6px; line-height: 1.5; }
.history-bottom { display: flex; justify-content: space-between; align-items: center; }
.history-customer { font-size: 0.7rem; color: #c8b090; }
.history-total { font-size: 0.88rem; font-weight: 700; color: #b8720a; }
.discount-pill { background: #edfaed; border: 1px solid #4caf50; color: #2e7d32; border-radius: 20px; padding: 2px 10px; font-size: 0.7rem; font-weight: 600; }

/* ═══════════════════════════════════════
   EMPTY STATE
═══════════════════════════════════════ */
.empty-state { text-align: center; padding: 3rem 2rem; }
.empty-state .icon { font-size: 2.5rem; margin-bottom: 0.8rem; opacity: 0.25; }
.empty-state p { font-size: 0.84rem; margin: 0; color: #c8b090; }

/* ═══════════════════════════════════════
   PENDING CARDS
═══════════════════════════════════════ */
.pending-card {
    background: #fff; border: 1.5px solid #e8dcc8; border-radius: 16px;
    margin-bottom: 16px; overflow: hidden;
    box-shadow: 0 2px 12px rgba(184,114,10,.06); transition: border-color 0.2s, box-shadow 0.2s;
}
.pending-card:hover { border-color: #e8a020; box-shadow: 0 6px 24px rgba(184,114,10,.14); }
.pending-card-header {
    background: #fffbf4; padding: 13px 18px;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid #f0e4cc;
}
.pending-token { font-size: 1rem; font-weight: 800; color: #b8720a; font-family: 'JetBrains Mono', monospace; }
.pending-time  { font-size: 0.7rem; color: #b8a080; background: #f5f0e8; padding: 3px 10px; border-radius: 20px; border: 1px solid #e8dcc8; }
.pending-status-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: #e8a020; margin-right: 8px; animation: pulse 1.5s infinite;
    box-shadow: 0 0 6px rgba(232,160,32,.5);
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.2; } }

/* ═══════════════════════════════════════
   LIVE COUNTER
═══════════════════════════════════════ */
.live-counter {
    background: linear-gradient(135deg, #fff8ec, #fffbf4);
    border: 1.5px solid #f5c842; border-radius: 16px; padding: 18px 24px;
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 1.6rem; box-shadow: 0 2px 12px rgba(184,114,10,.08);
}
.live-counter-label  { font-size: 0.62rem; color: #c8880e; text-transform: uppercase; letter-spacing: .1em; font-weight: 700; margin-bottom: 4px; }
.live-counter-value  { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: #b8720a; display: inline; }
.live-counter-amount { font-size: 0.88rem; color: #c8880e; font-weight: 600; margin-left: 14px; }

/* ═══════════════════════════════════════
   DATAFRAME LIGHT THEME
═══════════════════════════════════════ */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid #e8dcc8; }
[data-testid="stDataFrame"] table { background: #fff !important; }
[data-testid="stDataFrame"] th { background: #fffbf4 !important; color: #c8b090 !important; border-color: #e8dcc8 !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: .06em; }
[data-testid="stDataFrame"] td { color: #1a1208 !important; border-color: #f0e8d8 !important; font-size: 0.8rem !important; }
[data-testid="stDataFrame"] tr:hover td { background: #fffbf4 !important; }

/* ═══════════════════════════════════════
   FOOTER
═══════════════════════════════════════ */
.cafe-footer {
    text-align: center; padding: 2rem 0 1.5rem;
    color: #d4c0a0; font-size: 0.7rem; letter-spacing: 0.08em;
    border-top: 1px solid #e8dcc8; margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════════════════
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEET_HEADERS = ["Bill No","Date","Time","Customer","Token","Items (JSON)","Subtotal","Discount","Total"]

@st.cache_resource(show_spinner=False)
def get_worksheet():
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(SHEET_NAME)
        try:
            ws = sh.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=5000, cols=20)
            ws.append_row(SHEET_HEADERS)
        if ws.row_values(1) != SHEET_HEADERS:
            ws.insert_row(SHEET_HEADERS, 1)
        return ws, None
    except Exception as e:
        return None, str(e)

def append_bill_to_sheet(ws, bill):
    ws.append_row([
        bill["bill_no"],
        bill["timestamp"].strftime("%Y-%m-%d"),
        bill["timestamp"].strftime("%H:%M:%S"),
        bill["customer"], bill["token"],
        json.dumps(bill["items"], ensure_ascii=False),
        bill["subtotal"], bill["discount"], bill["total"],
    ], value_input_option="USER_ENTERED")

@st.cache_data(ttl=30, show_spinner=False)
def load_bills_from_sheet(_ws):
    bills = []
    for r in _ws.get_all_records():
        try:
            bills.append({
                "bill_no":   int(r["Bill No"]),
                "timestamp": datetime.strptime(f"{r['Date']} {r['Time']}", "%Y-%m-%d %H:%M:%S"),
                "items":     json.loads(r["Items (JSON)"]),
                "subtotal":  int(r["Subtotal"]),
                "discount":  int(r["Discount"]),
                "total":     int(r["Total"]),
                "customer":  r["Customer"],
                "token":     r["Token"],
            })
        except Exception:
            continue
    return bills

# ── Session state ──────────────────────────────────────────────────────────────
if "cart"           not in st.session_state: st.session_state.cart = {}
if "bill_counter"   not in st.session_state: st.session_state.bill_counter = None
if "pending_orders" not in st.session_state: st.session_state.pending_orders = []
if "confirm_reset"  not in st.session_state: st.session_state.confirm_reset = False

# ── Helpers ───────────────────────────────────────────────────────────────────
ALL_ITEMS = {k: v for cat in MENU.values() for k, v in cat.items()}

def calc_totals(cart):
    sub  = sum(ALL_ITEMS[n] * q for n, q in cart.items())
    disc = (sub * DISCOUNT_PCT // 100) if sub >= DISCOUNT_THRESHOLD else 0
    return sub, disc, sub - disc

def clean(name):
    return name.split("⭐")[0].split("🆕")[0].strip()

def bills_in_range(bills, s, e):
    return [b for b in bills if s <= b["timestamp"].date() <= e]

def sales_summary(bl):
    rev = sum(b["total"] for b in bl)
    cnt = len(bl)
    avg = rev / cnt if cnt else 0
    ic  = defaultdict(int)
    for b in bl:
        for n, q in b["items"].items(): ic[n] += q
    return rev, cnt, avg, sorted(ic.items(), key=lambda x: x[1], reverse=True)[:5]

def bar_chart_html(items, max_qty):
    if not items:
        return "<p style='color:#ccc;font-size:.8rem;padding:1rem 0'>No data yet.</p>"
    html = ""
    for name, qty in items:
        pct = (qty / max_qty * 100) if max_qty else 0
        html += (
            f"<div class='bar-row'>"
            f"<div class='bar-name' title='{name}'>{clean(name)[:22]}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{pct:.1f}%'></div></div>"
            f"<div class='bar-num'>{qty} pcs</div>"
            f"</div>"
        )
    return html

def make_bill_text(order):
    # Always use IST for timestamps
    ts = order["timestamp"]
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=IST)
    ts_ist = ts.astimezone(IST)

    W = 42  # fixed receipt width — pure ASCII only

    def ctr(t):
        # centre using spaces only — no unicode padding issues
        t = str(t)
        pad = max(0, W - len(t))
        return " " * (pad // 2) + t + " " * (pad - pad // 2)

    def rule(ch="-"):
        return ch * W

    lines = [
        ctr("* UPSARPANCH CHAIFI *"),
        ctr("The CHAI FI Caffe"),
        ctr("GF-27 Migsun Twiinz, Eta-2"),
        ctr("Greater Noida"),
        rule("."),
        f"  Bill  : #{order['bill_no']}",
        f"  Date  : {ts_ist.strftime('%d %b %Y')}",
        f"  Time  : {ts_ist.strftime('%I:%M %p')} IST",
    ]
    if order["customer"] not in ("Walk-in", ""):
        lines.append(f"  Name  : {order['customer']}")
    if order["token"] not in ("--", "-", "—", ""):
        lines.append(f"  Token : {order['token']}")

    lines += [
        rule(),
        f"  {'ITEM':<20} {'QTY':>4} {'AMT':>7}",
        rule(),
    ]
    for name, qty in order["items"].items():
        disp = clean(name)[:20]
        amt  = ALL_ITEMS[name] * qty
        lines.append(f"  {disp:<20} {qty:>4} Rs{amt:>5}")

    lines += [
        rule(),
        f"  {'Subtotal':<26} Rs{order['subtotal']:>5}",
    ]
    if order["discount"]:
        lines.append(f"  {'Discount (10% off)':<26}-Rs{order['discount']:>4}")
    lines += [
        rule("="),
        f"  {'TOTAL PAYABLE':<26} Rs{order['total']:>5}",
        rule("="),
        "",
        ctr("Ek Chai Ho Jaye? :)"),
        ctr("Thank you for visiting!"),
        ctr("* Warm Moments, Great Flavors *"),
    ]
    return "\n".join(lines)

# ── Connect to Google Sheets ───────────────────────────────────────────────────
ws, gs_error = get_worksheet()
if ws is not None:
    all_bills = load_bills_from_sheet(ws)
    if st.session_state.bill_counter is None:
        st.session_state.bill_counter = max((b["bill_no"] for b in all_bills), default=1000) + 1
else:
    all_bills = []
    if st.session_state.bill_counter is None:
        st.session_state.bill_counter = random.randint(1000, 1099)

# ══════════════════════════════════════════════════════════════════════════════
# APP HEADER
# ══════════════════════════════════════════════════════════════════════════════
gs_badge_html = (
    "<span class='badge badge-green'>● Sheets connected</span>"
    if ws is not None else
    "<span class='badge badge-red'>● Sheets offline</span>"
)
p_count_hdr = len(st.session_state.pending_orders)
p_total_hdr = sum(o["total"] for o in st.session_state.pending_orders)
st.markdown(
    f"<div class='hero'>"
    f"<div class='hero-left'>"
    f"<div class='hero-eyebrow'>Billing System</div>"
    f"<div class='hero-title'>Upsarpanch <span>ChaiFi</span></div>"
    f"<div class='hero-sub'>GF-27, Migsun Twiinz, Sector – Eta-2, Greater Noida</div>"
    f"</div>"
    f"<div class='hero-right'>"
    f"<div style='text-align:right'>"
    f"<div style='font-size:.62rem;color:#c8b090;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px'>Pending Orders</div>"
    f"<div style='font-size:1.4rem;font-weight:800;color:#b8720a;font-family:Playfair Display,serif;line-height:1'>{p_count_hdr}</div>"
    f"<div style='font-size:.72rem;color:#b8a080'>Rs {p_total_hdr:,} unpaid</div>"
    f"</div>"
    f"<div style='width:1px;height:40px;background:#e8dcc8;margin:0 4px'></div>"
    f"{gs_badge_html}"
    f"</div>"
    f"</div>",
    unsafe_allow_html=True,
)
# Add main content wrapper
st.markdown("<div class='main-wrap'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
pending_count = len(st.session_state.pending_orders)
tab_new, tab_pending, tab_sales, tab_table = st.tabs([
    "🛒  New Order",
    f"⏳  Pending Orders  ({pending_count})",
    "📊  Sales Dashboard",
    "📋  Orders Table",
])

# ════════════════════════ TAB 1 — NEW ORDER ═══════════════════════════════════
with tab_new:

    # ── Item picker (replaces sidebar) ────────────────────────────────────────
    st.markdown("<div class='picker-title'>Add Item to Order</div>", unsafe_allow_html=True)
    with st.container():
        pc1, pc2, pc3, pc4 = st.columns([1.6, 2.4, 0.8, 1.2])
        with pc1:
            category = st.selectbox("Category", list(MENU.keys()), label_visibility="collapsed")
        with pc2:
            item  = st.selectbox("Item", list(MENU[category].keys()), label_visibility="collapsed")
            price = MENU[category][item]
        with pc3:
            qty = st.number_input("Qty", min_value=1, max_value=20, value=1, step=1, label_visibility="collapsed")
        with pc4:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button(f"＋ Add  ·  ₹ {price * qty}", use_container_width=True):
                st.session_state.cart[item] = st.session_state.cart.get(item, 0) + qty
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Cart + Bill ───────────────────────────────────────────────────────────
    col_order, col_bill = st.columns([1.1, 1], gap="large")

    with col_order:
        # Cart count header
        cart_total_items = sum(st.session_state.cart.values())
        header_right = f"<span style='color:#b8720a;font-weight:700'>{cart_total_items} items</span>" if st.session_state.cart else ""
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem'>"
            f"<div class='section-title' style='margin:0'>Current Cart</div>"
            f"{header_right}"
            f"</div>",
            unsafe_allow_html=True,
        )

        if not st.session_state.cart:
            st.markdown(
                "<div class='empty-state'><div class='icon'>🛒</div>"
                "<p>Cart is empty.<br>Select an item above and click Add.</p></div>",
                unsafe_allow_html=True,
            )
        else:
            to_remove = []
            for idx, (name, qty) in enumerate(st.session_state.cart.items()):
                p = ALL_ITEMS[name]
                c1, c2, c3, c4 = st.columns([4, 1.2, 1.2, 0.6])
                c1.markdown(
                    f"<div style='padding:8px 0'>"
                    f"<div style='font-size:.86rem;font-weight:600;color:#1a1208'>{clean(name)}</div>"
                    f"<div style='font-size:.72rem;color:#b8a080'>₹ {p} each</div></div>",
                    unsafe_allow_html=True,
                )
                new_qty = c2.number_input("qty", min_value=0, max_value=50, value=qty,
                                          key=f"q{idx}", label_visibility="collapsed")
                if new_qty != qty:
                    if new_qty == 0: to_remove.append(name)
                    else: st.session_state.cart[name] = new_qty
                    st.rerun()
                c3.markdown(
                    f"<div style='padding:8px 0;text-align:right;font-weight:700;color:#b8720a'>₹ {p*qty}</div>",
                    unsafe_allow_html=True,
                )
                if c4.button("✕", key=f"d{idx}"): to_remove.append(name)
                st.markdown("<hr style='margin:2px 0'>", unsafe_allow_html=True)

            for n in to_remove: st.session_state.cart.pop(n, None)
            if to_remove: st.rerun()

            subtotal, discount_amt, total = calc_totals(st.session_state.cart)
            disc_color = "#2e7d32" if discount_amt else "#bbb"
            disc_val   = f"− ₹ {discount_amt}" if discount_amt else "—"
            st.markdown(
                f"<div class='totals-strip'>"
                f"<div class='totals-row'><span class='t-label'>Subtotal</span><span class='t-val'>₹ {subtotal}</span></div>"
                f"<div class='totals-row'><span class='t-label'>Discount (10%)</span><span style='color:{disc_color}'>{disc_val}</span></div>"
                f"<div class='totals-row grand'><span>Total Payable</span><span style='color:#b8720a'>₹ {total}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if subtotal < DISCOUNT_THRESHOLD:
                st.markdown(
                    f"<div class='nudge'>🏷️ Add ₹ {DISCOUNT_THRESHOLD - subtotal} more to unlock 10% off!</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🗑  Clear Cart", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

    with col_bill:
        st.markdown("<div class='section-title'>Order Details & Bill Preview</div>", unsafe_allow_html=True)
        customer = st.text_input("Customer Name", placeholder="Walk-in customer")
        token    = st.text_input("Table / Token No.", placeholder="e.g. T-3, Counter, Table-1")

        if st.session_state.cart:
            subtotal, discount_amt, total = calc_totals(st.session_state.cart)
            now     = datetime.now(IST)
            bill_no = st.session_state.bill_counter

            preview = {
                "bill_no": bill_no, "timestamp": now,
                "items": dict(st.session_state.cart),
                "subtotal": subtotal, "discount": discount_amt, "total": total,
                "customer": customer.strip() or "Walk-in",
                "token":    token.strip() or "—",
            }
            st.markdown(
                "<div style='background:#fefcf5;border-radius:14px;padding:6px 0 0 0;"
                "border:1px solid #e8d8a0;box-shadow:0 8px 40px rgba(0,0,0,.5);"
                "overflow:hidden;position:relative'>"
                "<div style='height:3px;background:linear-gradient(90deg,#9a5e08,#e8a020,#f5c842,#e8a020,#9a5e08)'></div>",
                unsafe_allow_html=True,
            )
            st.code(make_bill_text(preview), language=None)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='font-size:.73rem;color:#b8a080;margin-bottom:6px'>"
                "Customer pays later — order goes to the Pending queue.</p>",
                unsafe_allow_html=True,
            )
            if st.button("📋  Place Order → Pending", use_container_width=True):
                st.session_state.pending_orders.append({
                    "id":        random.randint(100000, 999999),
                    "bill_no":   bill_no,
                    "timestamp": now,
                    "items":     dict(st.session_state.cart),
                    "subtotal":  subtotal,
                    "discount":  discount_amt,
                    "total":     total,
                    "customer":  customer.strip() or "Walk-in",
                    "token":     token.strip() or "—",
                })
                st.session_state.cart = {}
                st.session_state.bill_counter += 1
                st.success(f"✅ Order #{bill_no} placed! Go to ⏳ Pending Orders to mark as paid.")
                st.rerun()
        else:
            st.markdown(
                "<div class='empty-state'><div class='icon'>🧾</div>"
                "<p>Bill preview will appear<br>once you add items.</p></div>",
                unsafe_allow_html=True,
            )

# ════════════════════════ TAB 2 — PENDING ORDERS ══════════════════════════════
with tab_pending:
    pending = st.session_state.pending_orders

    # track which order is in edit mode: {order_id: True/False}
    if "editing_order" not in st.session_state:
        st.session_state.editing_order = {}

    if not pending:
        st.markdown(
            "<div class='empty-state' style='padding:4rem'>"
            "<div class='icon'>✅</div>"
            "<p style='font-size:1rem;font-weight:700;color:#4caf50'>All clear!</p>"
            "<p style='margin-top:6px'>No pending orders. All bills have been paid.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        total_pending_amt = sum(o["total"] for o in pending)
        st.markdown(
            f"<div class='live-counter'>"
            f"<div><div class='live-counter-label'>Orders waiting for payment</div>"
            f"<div><span class='live-counter-value'>{len(pending)} orders</span>"
            f"<span class='live-counter-amount'>· ₹ {total_pending_amt:,} total unpaid</span></div></div>"
            f"<div style='font-size:2.5rem;opacity:.3'>⏳</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        to_remove_ids = []

        for order in pending:
            oid        = order["id"]
            is_editing = st.session_state.editing_order.get(oid, False)

            token_html = (
                f"<span style='font-size:.78rem;color:#b8720a;background:#fff8ec;"
                f"padding:2px 10px;border-radius:8px;font-weight:600;margin-left:8px'>{order['token']}</span>"
                if order["token"] != "—" else ""
            )

            # Recalculate totals (may have been edited)
            sub, disc, tot = calc_totals(order["items"])
            order["subtotal"] = sub
            order["discount"] = disc
            order["total"]    = tot

            disc_html = (
                f"<span style='font-size:.75rem;color:#2e7d32;background:#edfaed;"
                f"padding:2px 10px;border-radius:20px;font-weight:600'>🏷 -₹{disc}</span>"
                if disc else ""
            )
            item_summary = ", ".join(f"{clean(n)} ×{q}" for n, q in order["items"].items())

            # Card border changes when editing
            edit_border = "border-color:#b8720a;box-shadow:0 0 0 3px rgba(184,114,10,.12);" if is_editing else ""

            st.markdown(
                f"<div class='pending-card' style='{edit_border}'>"
                f"<div class='pending-card-header'>"
                f"<div style='display:flex;align-items:center;flex-wrap:wrap;gap:6px'>"
                f"<span class='pending-status-dot'></span>"
                f"<span class='pending-token'>#{order['bill_no']}</span>"
                f"{token_html}"
                f"<span style='font-size:.78rem;color:#a89878;margin-left:4px'>{order['customer']}</span>"
                f"</div>"
                f"<span class='pending-time'>{order['timestamp'].strftime('%I:%M %p')}</span>"
                f"</div>"
                f"<div style='padding:16px 18px;display:flex;justify-content:space-between;align-items:center'>"
                f"<div style='font-size:.78rem;color:#a89878;max-width:60%'>{item_summary}</div>"
                f"<div style='text-align:right'>"
                f"<div style='font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:#c8b090;font-weight:700'>Total Due</div>"
                f"<div style='font-size:1.7rem;font-weight:800;color:#b8720a;line-height:1.1'>₹ {tot}</div>"
                f"<div style='margin-top:4px'>{disc_html}</div>"
                f"</div></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── EDIT PANEL (shown when editing) ───────────────────────────────
            if is_editing:
                st.markdown(
                    "<div style='background:#fffbf4;border:1.5px solid #f0e0b0;border-radius:14px;"
                    "padding:16px 18px;margin-top:-6px;margin-bottom:6px'>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='font-size:.68rem;font-weight:700;text-transform:uppercase;"
                    "letter-spacing:.1em;color:#b8720a;margin-bottom:10px'>✏️ Edit Order Items</div>",
                    unsafe_allow_html=True,
                )

                # Existing items — edit qty or remove
                items_to_remove = []
                for eidx, (iname, iqty) in enumerate(list(order["items"].items())):
                    iprice = ALL_ITEMS[iname]
                    ec1, ec2, ec3, ec4 = st.columns([4, 1.3, 1.3, 0.7])
                    ec1.markdown(
                        f"<div style='padding:6px 0'>"
                        f"<div style='font-size:.84rem;font-weight:600;color:#1a1208'>{clean(iname)}</div>"
                        f"<div style='font-size:.7rem;color:#b8a080'>₹ {iprice} each</div></div>",
                        unsafe_allow_html=True,
                    )
                    new_iqty = ec2.number_input(
                        "qty", min_value=0, max_value=50, value=iqty,
                        key=f"eq_{oid}_{eidx}", label_visibility="collapsed"
                    )
                    if new_iqty != iqty:
                        if new_iqty == 0:
                            items_to_remove.append(iname)
                        else:
                            order["items"][iname] = new_iqty
                        st.rerun()
                    ec3.markdown(
                        f"<div style='padding:6px 0;text-align:right;font-weight:700;color:#b8720a'>₹ {iprice * iqty}</div>",
                        unsafe_allow_html=True,
                    )
                    if ec4.button("✕", key=f"erm_{oid}_{eidx}"):
                        items_to_remove.append(iname)

                for n in items_to_remove:
                    order["items"].pop(n, None)
                if items_to_remove:
                    st.rerun()

                # Add new item row
                st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
                st.markdown(
                    "<div style='font-size:.68rem;color:#c8b090;font-weight:600;margin-bottom:6px'>ADD ITEM</div>",
                    unsafe_allow_html=True,
                )
                na1, na2, na3, na4 = st.columns([1.6, 2.4, 0.8, 1.2])
                with na1:
                    add_cat  = st.selectbox("Cat", list(MENU.keys()), key=f"ecat_{oid}", label_visibility="collapsed")
                with na2:
                    add_item = st.selectbox("Item", list(MENU[add_cat].keys()), key=f"eitm_{oid}", label_visibility="collapsed")
                with na3:
                    add_qty  = st.number_input("Qty", min_value=1, max_value=20, value=1, key=f"eqty_{oid}", label_visibility="collapsed")
                with na4:
                    add_price = MENU[add_cat][add_item]
                    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                    if st.button(f"＋ Add · ₹{add_price * add_qty}", key=f"eadd_{oid}", use_container_width=True):
                        order["items"][add_item] = order["items"].get(add_item, 0) + add_qty
                        st.rerun()

                # Save / discard edit
                st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
                sv1, sv2 = st.columns(2, gap="medium")
                with sv1:
                    if st.button("💾  Save Changes", key=f"esave_{oid}", use_container_width=True):
                        st.session_state.editing_order[oid] = False
                        st.success("Order updated!")
                        st.rerun()
                with sv2:
                    if st.button("✕  Discard", key=f"edisc_{oid}", use_container_width=True):
                        st.session_state.editing_order[oid] = False
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

            # ── ACTION BUTTONS ────────────────────────────────────────────────
            bc1, bc2, bc3, bc4 = st.columns([2.2, 0.9, 0.85, 0.85])
            with bc1:
                if st.button(f"✅  Mark as Paid  ·  ₹ {tot}", key=f"pay_{oid}", use_container_width=True):
                    to_remove_ids.append(oid)
                    if ws is not None:
                        try:
                            append_bill_to_sheet(ws, order)
                            load_bills_from_sheet.clear()
                        except Exception as e:
                            st.error(f"Sheet save failed: {e}")
                    st.success(f"💰 Bill #{order['bill_no']} marked as paid!")
            with bc2:
                edit_label = "✕ Close" if is_editing else "✏️  Edit"
                if st.button(edit_label, key=f"edit_{oid}", use_container_width=True):
                    st.session_state.editing_order[oid] = not is_editing
                    st.rerun()
            with bc3:
                st.download_button(
                    "⬇  Bill", data=make_bill_text(order),
                    file_name=f"ChaiFi_Bill_{order['bill_no']}.txt",
                    mime="text/plain", key=f"dl_{oid}", use_container_width=True,
                )
            with bc4:
                if st.button("🗑 Cancel", key=f"cancel_{oid}", use_container_width=True):
                    to_remove_ids.append(oid)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if to_remove_ids:
            st.session_state.pending_orders = [o for o in st.session_state.pending_orders if o["id"] not in to_remove_ids]
            # clean up edit state for removed orders
            for rid in to_remove_ids:
                st.session_state.editing_order.pop(rid, None)
            st.rerun()

# ════════════════════════ TAB 3 — SALES DASHBOARD ════════════════════════════
with tab_sales:
    if ws is not None:
        all_bills = load_bills_from_sheet(ws)

    today       = date.today()
    week_start  = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    day_bills   = bills_in_range(all_bills, today,       today)
    week_bills  = bills_in_range(all_bills, week_start,  today)
    month_bills = bills_in_range(all_bills, month_start, today)

    day_rev, day_cnt, day_avg, _ = sales_summary(day_bills)
    wk_rev,  wk_cnt,  wk_avg,  _ = sales_summary(week_bills)
    mo_rev,  mo_cnt,  mo_avg,  _ = sales_summary(month_bills)

    st.markdown("<div class='section-title'>Revenue at a Glance</div>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3, gap="medium")
    for col, icon, label, rev, cnt, avg in [
        (k1, "📅", "Today",      day_rev, day_cnt, day_avg),
        (k2, "📆", "This Week",  wk_rev,  wk_cnt,  wk_avg),
        (k3, "🗓️", "This Month", mo_rev,  mo_cnt,  mo_avg),
    ]:
        col.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{icon} {label}</div>"
            f"<div class='kpi-value'>₹ {rev:,}</div>"
            f"<div class='kpi-sub'>{cnt} bills · avg ₹ {avg:.0f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    ch1, ch2 = st.columns(2, gap="medium")

    with ch1:
        period = st.selectbox("Period", ["Today","This Week","This Month"], key="period_sel")
        pmap   = {"Today": day_bills, "This Week": week_bills, "This Month": month_bills}
        _, _, _, top_items = sales_summary(pmap[period])
        max_q  = top_items[0][1] if top_items else 1
        st.markdown(
            f"<div class='chart-card'><div class='chart-card-title'>🏆 Top Selling — {period}</div>"
            + bar_chart_html(top_items, max_q) + "</div>",
            unsafe_allow_html=True,
        )

    with ch2:
        day_labels = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        day_revs   = [sum(b["total"] for b in bills_in_range(all_bills, d, d)) for d in day_labels]
        max_r      = max(day_revs) if any(day_revs) else 1
        rev_rows   = "".join(
            f"<div class='bar-row'><div class='bar-name'>{d.strftime('%a %d')}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{(r/max_r*100) if max_r else 0:.1f}%'></div></div>"
            f"<div class='bar-num'>₹ {r:,}</div></div>"
            for d, r in zip(day_labels, day_revs)
        )
        st.markdown(
            "<div class='chart-card'><div class='chart-card-title'>📈 Daily Revenue — Last 7 Days</div>"
            + (rev_rows if any(day_revs) else "<p style='color:#ccc;font-size:.8rem;padding:1rem 0'>No data yet.</p>")
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Bill History (Paid)</div>", unsafe_allow_html=True)

    hperiod = st.selectbox("Show", ["Today","This Week","This Month","All Time"], key="hist_sel")
    hmap    = {"Today": day_bills, "This Week": week_bills, "This Month": month_bills, "All Time": all_bills}
    hbills  = list(reversed(hmap[hperiod]))

    if not hbills:
        st.markdown("<div class='empty-state'><div class='icon'>📋</div><p>No paid bills in this period.</p></div>", unsafe_allow_html=True)
    else:
        for b in hbills:
            items_str = " · ".join(f"{clean(n)} ×{q}" for n, q in b["items"].items())
            disc_str  = f"&nbsp;<span class='discount-pill'>-₹{b['discount']}</span>" if b["discount"] else ""
            st.markdown(
                f"<div class='history-card'>"
                f"<div class='history-top'><span class='history-bill'>#{b['bill_no']}</span>"
                f"<span class='history-time'>{b['timestamp'].strftime('%d %b %Y · %I:%M %p')}</span></div>"
                f"<div class='history-items'>{items_str}</div>"
                f"<div class='history-bottom'><span class='history-customer'>👤 {b['customer']}</span>"
                f"<span class='history-total'>₹ {b['total']}{disc_str}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Sheet management ──────────────────────────────────────────────────────
    if ws is not None:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>⚙️ Sheet Management</div>", unsafe_allow_html=True)

        m1, m2 = st.columns(2, gap="medium")
        with m1:
            if st.button("🔄  Refresh from Google Sheets", use_container_width=True):
                load_bills_from_sheet.clear()
                st.rerun()
        with m2:
            if st.button("🗑️  Reset All Sheet Data", use_container_width=True):
                st.session_state.confirm_reset = True

        if st.session_state.confirm_reset:
            st.markdown(
                "<div style='background:#fff5f5;border:1.5px solid #f44336;border-radius:12px;"
                "padding:16px 20px;margin-top:12px'>"
                "<div style='font-weight:700;color:#c62828;font-size:.9rem;margin-bottom:6px'>"
                "⚠️ Are you sure you want to reset all data?</div>"
                "<div style='font-size:.8rem;color:#888'>This will permanently delete all bill records "
                "from the Google Sheet and reset the bill counter to #1001. This cannot be undone.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                if st.button("✅  Yes, Reset Everything", use_container_width=True):
                    try:
                        ws.clear()
                        ws.append_row(SHEET_HEADERS)
                        st.session_state.bill_counter   = 1001
                        st.session_state.pending_orders = []
                        st.session_state.cart           = {}
                        st.session_state.confirm_reset  = False
                        load_bills_from_sheet.clear()
                        st.success("✅ Sheet reset! Bill counter starts from #1001.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reset failed: {e}")
            with c2:
                if st.button("✕  Cancel", use_container_width=True):
                    st.session_state.confirm_reset = False
                    st.rerun()

# ════════════════════════ TAB 4 — ORDERS TABLE ═══════════════════════════════
with tab_table:
    if ws is not None:
        all_bills = load_bills_from_sheet(ws)

    st.markdown("<div class='section-title'>All Orders — Till Date</div>", unsafe_allow_html=True)

    if not all_bills:
        st.markdown(
            "<div class='empty-state'><div class='icon'>📋</div>"
            "<p>No orders recorded yet.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        import pandas as pd

        # ── Build dataframe ────────────────────────────────────────────────────
        rows = []
        for b in all_bills:
            items_str = ", ".join(f"{clean(n)} x{q}" for n, q in b["items"].items())
            rows.append({
                "Bill No":    f"#{b['bill_no']}",
                "Date":       b["timestamp"].strftime("%d %b %Y"),
                "Time":       b["timestamp"].strftime("%I:%M %p"),
                "Customer":   b["customer"],
                "Token":      b["token"],
                "Items":      items_str,
                "Subtotal":   b["subtotal"],
                "Discount":   b["discount"],
                "Total (Rs)": b["total"],
            })

        df_all = pd.DataFrame(rows)

        # ── Filters row ────────────────────────────────────────────────────────
        f1, f2, f3 = st.columns([1.5, 1.5, 1])
        with f1:
            search_q = st.text_input("🔍 Search customer / token / item", placeholder="Type to filter...", key="tbl_search")
        with f2:
            date_filter = st.selectbox(
                "📅 Date range",
                ["All Time", "Today", "This Week", "This Month"],
                key="tbl_date"
            )
        with f3:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            sort_desc = st.checkbox("Newest first", value=True, key="tbl_sort")

        # Apply date filter
        today_d     = date.today()
        week_start_d  = today_d - timedelta(days=today_d.weekday())
        month_start_d = today_d.replace(day=1)

        def date_filter_fn(b):
            bd = b["timestamp"].date()
            if date_filter == "Today":      return bd == today_d
            if date_filter == "This Week":  return bd >= week_start_d
            if date_filter == "This Month": return bd >= month_start_d
            return True

        filtered_bills = [b for b in all_bills if date_filter_fn(b)]

        # Apply search filter
        if search_q.strip():
            q = search_q.strip().lower()
            filtered_bills = [
                b for b in filtered_bills
                if q in b["customer"].lower()
                or q in b["token"].lower()
                or any(q in clean(n).lower() for n in b["items"])
                or q in str(b["bill_no"])
            ]

        # Sort
        filtered_bills = sorted(filtered_bills, key=lambda b: b["timestamp"], reverse=sort_desc)

        # Rebuild df from filtered list
        rows_f = []
        for b in filtered_bills:
            items_str = ", ".join(f"{clean(n)} x{q}" for n, q in b["items"].items())
            rows_f.append({
                "Bill No":    f"#{b['bill_no']}",
                "Date":       b["timestamp"].strftime("%d %b %Y"),
                "Time":       b["timestamp"].strftime("%I:%M %p"),
                "Customer":   b["customer"],
                "Token":      b["token"],
                "Items":      items_str,
                "Subtotal":   b["subtotal"],
                "Discount":   b["discount"],
                "Total (Rs)": b["total"],
            })
        df = pd.DataFrame(rows_f) if rows_f else pd.DataFrame(columns=list(df_all.columns))

        # ── Summary strip above table ──────────────────────────────────────────
        if rows_f:
            total_rev  = sum(b["total"]    for b in filtered_bills)
            total_disc = sum(b["discount"] for b in filtered_bills)
            n_bills    = len(filtered_bills)
            s1, s2, s3, s4 = st.columns(4, gap="medium")
            for col, label, val in [
                (s1, "Orders Shown",    str(n_bills)),
                (s2, "Total Revenue",   f"Rs {total_rev:,}"),
                (s3, "Total Discounts", f"Rs {total_disc:,}"),
                (s4, "Avg Bill Value",  f"Rs {total_rev//n_bills if n_bills else 0:,}"),
            ]:
                col.markdown(
                    f"<div style='background:#fff;border:1px solid #e8e4dc;border-radius:12px;"
                    f"padding:12px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);margin-bottom:10px'>"
                    f"<div style='font-size:.65rem;font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:.1em;color:#bbb;margin-bottom:4px'>{label}</div>"
                    f"<div style='font-size:1.2rem;font-weight:800;color:#b8720a'>{val}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # ── Table ─────────────────────────────────────────────────────────────
        if df.empty:
            st.info("No orders match your filter.")
        else:
            st.dataframe(
                df,
                use_container_width=True,
                height=min(40 + len(df) * 35, 500),
                column_config={
                    "Bill No":    st.column_config.TextColumn("Bill No",    width="small"),
                    "Date":       st.column_config.TextColumn("Date",       width="small"),
                    "Time":       st.column_config.TextColumn("Time",       width="small"),
                    "Customer":   st.column_config.TextColumn("Customer",   width="medium"),
                    "Token":      st.column_config.TextColumn("Token",      width="small"),
                    "Items":      st.column_config.TextColumn("Items",      width="large"),
                    "Subtotal":   st.column_config.NumberColumn("Subtotal", format="Rs %d", width="small"),
                    "Discount":   st.column_config.NumberColumn("Discount", format="Rs %d", width="small"),
                    "Total (Rs)": st.column_config.NumberColumn("Total",    format="Rs %d", width="small"),
                },
                hide_index=True,
            )

            # ── Download buttons ───────────────────────────────────────────────
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            dl1, dl2 = st.columns(2, gap="medium")

            # CSV download
            with dl1:
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "⬇  Download as CSV",
                    data=csv_data,
                    file_name=f"ChaiFi_Orders_{date.today().strftime('%d%b%Y')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_csv",
                )

            # Excel download
            with dl2:
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="ChaiFi Orders")
                    # Auto-fit columns
                    ws_xl = writer.sheets["ChaiFi Orders"]
                    for col_cells in ws_xl.columns:
                        max_len = max(len(str(c.value or "")) for c in col_cells) + 3
                        ws_xl.column_dimensions[col_cells[0].column_letter].width = min(max_len, 40)
                excel_buf.seek(0)
                st.download_button(
                    "⬇  Download as Excel (.xlsx)",
                    data=excel_buf.getvalue(),
                    file_name=f"ChaiFi_Orders_{date.today().strftime('%d%b%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_xlsx",
                )

    # Refresh button
    if ws is not None:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🔄  Refresh Data", key="tbl_refresh", use_container_width=False):
            load_bills_from_sheet.clear()
            st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)  # close main-wrap
st.markdown(
    "<div class='cafe-footer'>"
    "☕ &nbsp; UPSARPANCH CHAIFI &nbsp; · &nbsp; I ❤️ Upsarpanch &nbsp; · &nbsp; 10% off on orders above Rs 150"
    "</div>",
    unsafe_allow_html=True,
)
