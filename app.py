import streamlit as st
from datetime import datetime, date, timedelta
import random
import json
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="ChaiFi – Billing",
    page_icon="☕",
    layout="wide",
)

# ── Menu ──────────────────────────────────────────────────────────────────────
MENU = {
    "🍵 Beverages": {
        "Spl Gud ki Chai (Cup)":              15,
        "Spl Gud ki Chai (Khulad)":           20,
        "Lemon / Green / Black Tea":          30,
        "Cold Coffee ⭐ Must Try":             70,
        "Spl Masala Banta Soda ⭐":           40,
        "Regular Lassi":                      50,
        "Mango Lassi":                        60,
        "Kesar Badam Lassi":                  70,
    },
    "🍽️ Food Items": {
        "Bun Maska":                          40,
        "Plain Maggi":                        50,
        "Veg Maggi":                          60,
        "Grilled Aaloo Stuffed Patties ⭐":   60,
        "Grilled Paneer Stuffed Patties ⭐":  70,
        "Butter Masala Sweet Corn (S)":       50,
        "Butter Masala Sweet Corn (L)":       70,
        "Kulcha Pizza 🆕":                   100,
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
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; }
.stApp { background: #0d0d0d; color: #e8e0d0; font-family: 'Sora', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 2rem 2rem !important; max-width: 1400px; }

/* Sidebar */
[data-testid="stSidebar"] { background: #111111 !important; border-right: 1px solid #2a2a2a !important; padding-top: 0 !important; }
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
[data-testid="stSidebar"] * { color: #e8e0d0 !important; font-family: 'Sora', sans-serif !important; }

.sidebar-banner { background: linear-gradient(135deg, #b8720a 0%, #e8a020 50%, #f5c842 100%); margin: -1rem -1rem 1.5rem -1rem; padding: 1.5rem 1.2rem 1.2rem; text-align: center; }
.sidebar-banner h2 { color: #0d0d0d !important; font-size: 1.1rem !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: 0.05em; }
.sidebar-banner p { color: #3a2000 !important; font-size: 0.7rem !important; margin: 2px 0 0 !important; opacity: 0.8; }

/* Inputs */
input, textarea, select, div[data-baseweb="input"] input, div[data-baseweb="select"] div { background: #1a1a1a !important; color: #e8e0d0 !important; border-color: #2a2a2a !important; border-radius: 10px !important; font-family: 'Sora', sans-serif !important; }
div[data-baseweb="input"] { border-radius: 10px !important; background: #1a1a1a !important; }
.stSelectbox > div > div { background: #1a1a1a !important; border-color: #2a2a2a !important; border-radius: 10px !important; }
input[type="number"] { background: #1a1a1a !important; color: #e8e0d0 !important; border: 1px solid #2a2a2a !important; border-radius: 10px !important; }
label, .stSelectbox label, .stNumberInput label, .stTextInput label { color: #888 !important; font-size: 0.75rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em; }

/* Buttons */
.stButton > button { background: linear-gradient(135deg, #b8720a, #e8a020, #f5c842) !important; color: #0d0d0d !important; font-weight: 700 !important; font-family: 'Sora', sans-serif !important; border: none !important; border-radius: 10px !important; padding: 0.55rem 1.2rem !important; font-size: 0.88rem !important; letter-spacing: 0.02em; transition: all 0.2s ease !important; box-shadow: 0 4px 15px rgba(232,160,32,0.25) !important; }
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(232,160,32,0.4) !important; }
.stDownloadButton > button { background: #1a1a1a !important; color: #e8a020 !important; border: 1px solid #e8a020 !important; border-radius: 10px !important; font-weight: 600 !important; font-family: 'Sora', sans-serif !important; font-size: 0.88rem !important; transition: all 0.2s !important; }
.stDownloadButton > button:hover { background: #e8a020 !important; color: #0d0d0d !important; }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] { background: #111; border-radius: 12px; padding: 4px; border: 1px solid #2a2a2a; gap: 4px; }
button[data-baseweb="tab"] { background: transparent !important; color: #666 !important; border-radius: 8px !important; font-family: 'Sora', sans-serif !important; font-weight: 600 !important; font-size: 0.85rem !important; padding: 0.5rem 1.2rem !important; transition: all 0.2s !important; border: none !important; }
button[data-baseweb="tab"][aria-selected="true"] { background: linear-gradient(135deg, #b8720a, #e8a020) !important; color: #0d0d0d !important; }
[data-testid="stTabs"] [role="tabpanel"] { padding-top: 1.5rem; }

/* Metrics */
[data-testid="stMetricValue"] { color: #f5c842 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #666 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="metric-container"] { background: #111; border: 1px solid #2a2a2a; border-radius: 14px; padding: 1rem 1.2rem; }

hr { border: none !important; border-top: 1px solid #2a2a2a !important; margin: 1.2rem 0 !important; }
.stAlert { border-radius: 10px !important; font-family: 'Sora', sans-serif !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

/* App header */
.app-header { background: linear-gradient(135deg, #111 0%, #1a1200 100%); border-bottom: 1px solid #2a2a2a; padding: 1.2rem 2rem; margin: 0 -2rem 1.5rem -2rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.8rem; }
.app-header h1 { font-size: 1.5rem !important; font-weight: 800 !important; color: #f5c842 !important; margin: 0 !important; letter-spacing: -0.02em; }
.app-header p { font-size: 0.75rem; color: #666; margin: 2px 0 0 0; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em; }
.badge-green { background: #0f2a0f; border: 1px solid #2d7a2d; color: #5dc95d; }
.badge-red   { background: #2a0a0a; border: 1px solid #7a2d2d; color: #c95d5d; }

/* Section title */
.section-title { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #666; margin-bottom: 0.8rem; }

/* Totals strip */
.totals-strip { background: #111; border: 1px solid #2a2a2a; border-radius: 14px; padding: 1rem 1.2rem; margin-top: 0.8rem; }
.totals-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.85rem; }
.totals-row.grand { border-top: 1px solid #2a2a2a; margin-top: 8px; padding-top: 10px; font-size: 1.1rem; font-weight: 700; }
.totals-row .t-label { color: #888; }
.totals-row .t-val { color: #e8e0d0; }
.nudge { background: #1a1200; border: 1px dashed #b8720a; border-radius: 10px; padding: 10px 14px; font-size: 0.8rem; color: #e8a020; margin-top: 8px; text-align: center; }

/* Bill receipt */
.bill-receipt { background: #fefdf8; border-radius: 16px; padding: 28px 32px; border: 1px solid #e8d8b0; box-shadow: 0 8px 32px rgba(0,0,0,0.4); font-family: 'JetBrains Mono', monospace; color: #1a1200; position: relative; overflow: hidden; }
.bill-receipt::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #b8720a, #e8a020, #f5c842, #e8a020, #b8720a); }
.bill-receipt pre { margin: 0; font-size: 0.78rem; line-height: 1.9; background: transparent; color: #1a1200; white-space: pre; font-family: 'JetBrains Mono', monospace; }

/* KPI card */
.kpi-card { background: #111; border: 1px solid #2a2a2a; border-radius: 16px; padding: 1.2rem 1.4rem; transition: border-color 0.2s, transform 0.2s; }
.kpi-card:hover { border-color: #e8a020; transform: translateY(-2px); }
.kpi-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #555; margin-bottom: 6px; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: #f5c842; line-height: 1; margin-bottom: 4px; }
.kpi-sub { font-size: 0.75rem; color: #555; }

/* Charts */
.bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.bar-name { font-size: 0.75rem; color: #888; width: 150px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; background: #1a1a1a; border-radius: 6px; height: 20px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #b8720a, #f5c842); }
.bar-num { font-size: 0.75rem; color: #e8e0d0; font-weight: 600; width: 55px; text-align: right; flex-shrink: 0; }
.chart-card { background: #111; border: 1px solid #2a2a2a; border-radius: 16px; padding: 1.2rem 1.4rem; }
.chart-card-title { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #555; margin-bottom: 1rem; }

/* History card */
.history-card { background: #111; border: 1px solid #2a2a2a; border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; }
.history-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.history-bill { font-size: 0.8rem; font-weight: 700; color: #f5c842; font-family: 'JetBrains Mono', monospace; }
.history-time { font-size: 0.72rem; color: #555; }
.history-items { font-size: 0.78rem; color: #888; margin-bottom: 6px; line-height: 1.5; }
.history-bottom { display: flex; justify-content: space-between; align-items: center; }
.history-customer { font-size: 0.72rem; color: #555; }
.history-total { font-size: 0.88rem; font-weight: 700; color: #e8a020; }
.discount-pill { background: #0f2a0f; border: 1px solid #2d7a2d; color: #5dc95d; border-radius: 20px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }

/* Empty state */
.empty-state { text-align: center; padding: 3rem 2rem; color: #444; }
.empty-state .icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.4; }
.empty-state p { font-size: 0.85rem; margin: 0; }

/* ══ PENDING ORDER CARDS ══ */
.pending-card {
    background: #111;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 0;
    margin-bottom: 14px;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.pending-card:hover {
    border-color: #3a3a3a;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.pending-card-header {
    background: #161616;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #2a2a2a;
}
.pending-token {
    font-size: 1rem;
    font-weight: 800;
    color: #f5c842;
    font-family: 'JetBrains Mono', monospace;
}
.pending-time {
    font-size: 0.72rem;
    color: #555;
}
.pending-card-body {
    padding: 12px 16px;
}
.pending-items-list {
    font-size: 0.8rem;
    color: #aaa;
    margin-bottom: 10px;
    line-height: 1.7;
}
.pending-amount {
    font-size: 1.3rem;
    font-weight: 800;
    color: #e8a020;
}
.pending-status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #e8a020;
    margin-right: 6px;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
.paid-flash {
    background: #0f2a0f;
    border-color: #2d7a2d;
}

/* Live orders counter */
.live-counter {
    background: #1a1200;
    border: 1px solid #b8720a;
    border-radius: 12px;
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
}
.live-counter-label { font-size: 0.72rem; color: #888; text-transform: uppercase; letter-spacing: 0.08em; }
.live-counter-value { font-size: 1.4rem; font-weight: 800; color: #f5c842; }
.live-counter-amount { font-size: 0.9rem; color: #e8a020; font-weight: 600; }
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
if "cart"            not in st.session_state: st.session_state.cart = {}
if "bill_counter"    not in st.session_state: st.session_state.bill_counter = None
if "pending_orders"  not in st.session_state: st.session_state.pending_orders = []
# pending_orders: list of dicts
#   { id, bill_no, timestamp, items, subtotal, discount, total, customer, token }

# ── Helpers ───────────────────────────────────────────────────────────────────
ALL_ITEMS = {k: v for cat in MENU.values() for k, v in cat.items()}

def calc_totals(cart):
    sub  = sum(ALL_ITEMS[n] * q for n, q in cart.items())
    disc = (sub * DISCOUNT_PCT // 100) if sub >= DISCOUNT_THRESHOLD else 0
    return sub, disc, sub - disc

def bills_in_range(bills, s, e):
    return [b for b in bills if s <= b["timestamp"].date() <= e]

def sales_summary(bl):
    rev = sum(b["total"] for b in bl)
    cnt = len(bl)
    avg = rev / cnt if cnt else 0
    ic  = defaultdict(int)
    for b in bl:
        for n, q in b["items"].items(): ic[n] += q
    top = sorted(ic.items(), key=lambda x: x[1], reverse=True)[:5]
    return rev, cnt, avg, top

def bar_chart_html(items, max_qty):
    if not items:
        return "<p style='color:#444;font-size:.8rem;padding:1rem 0'>No data yet.</p>"
    html = ""
    for name, qty in items:
        pct   = (qty / max_qty * 100) if max_qty else 0
        label = name.split("⭐")[0].split("🆕")[0].strip()[:22]
        html += (
            f"<div class='bar-row'>"
            f"<div class='bar-name' title='{name}'>{label}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{pct:.1f}%'></div></div>"
            f"<div class='bar-num'>{qty} pcs</div>"
            f"</div>"
        )
    return html

def make_bill_text(order):
    lines = [
        f"{'★  UPSARPANCH  CHAIFI  ★':^44}",
        f"{'The CHAI FI Caffe':^44}",
        f"{'GF-27 Migsun Twiinz, Eta-2':^44}",
        f"{'Greater Noida':^44}",
        "·" * 44,
        f"  Bill No : #{order['bill_no']:<10} Date: {order['timestamp'].strftime('%d %b %Y')}",
        f"  Time    : {order['timestamp'].strftime('%I:%M %p')}",
    ]
    if order["customer"] != "Walk-in": lines.append(f"  Customer: {order['customer']}")
    if order["token"] != "—":          lines.append(f"  Token   : {order['token']}")
    lines += ["─" * 44, f"  {'ITEM':<24}{'QTY':>5}  {'AMT':>8}", "─" * 44]
    for name, qty in order["items"].items():
        p    = ALL_ITEMS[name]
        rt   = p * qty
        disp = name.split("⭐")[0].split("🆕")[0].strip()[:22]
        lines.append(f"  {disp:<24}{qty:>5}  ₹{rt:>6}")
    lines += ["─" * 44, f"  {'Subtotal':<30}₹{order['subtotal']:>8}"]
    if order["discount"]:
        lines.append(f"  {'Discount (10% off ₹150+)':<30}-₹{order['discount']:>7}")
    lines += [
        "═" * 44,
        f"  {'TOTAL PAYABLE':<30}₹{order['total']:>8}",
        "═" * 44,
        "",
        f"{'Ek Chai Ho Jaye? ☕':^44}",
        f"{'Thank you for visiting!':^44}",
    ]
    return "\n".join(lines)

# ── Connect ───────────────────────────────────────────────────────────────────
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
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class='sidebar-banner'>
        <h2>☕ UPSARPANCH CHAIFI</h2>
        <p>Warm Moments, Great Flavors</p>
    </div>
    """, unsafe_allow_html=True)

    category = st.selectbox("Category", list(MENU.keys()))
    item     = st.selectbox("Item", list(MENU[category].keys()))
    price    = MENU[category][item]
    qty      = st.number_input("Quantity", min_value=1, max_value=20, value=1, step=1)

    st.markdown(
        f"<div style='background:#1a1200;border:1px solid #3a2a00;border-radius:10px;"
        f"padding:10px 14px;margin:8px 0;display:flex;justify-content:space-between;align-items:center'>"
        f"<span style='color:#888;font-size:.8rem'>Subtotal</span>"
        f"<span style='color:#f5c842;font-weight:700;font-size:.95rem'>₹ {price * qty}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if st.button("＋  Add to Order", use_container_width=True):
        st.session_state.cart[item] = st.session_state.cart.get(item, 0) + qty
        st.success(f"Added {qty}× {item.split('⭐')[0].split('🆕')[0].strip()}")

    if st.session_state.cart:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("🗑  Clear Cart", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Live pending summary in sidebar
    pending_count = len(st.session_state.pending_orders)
    pending_total = sum(o["total"] for o in st.session_state.pending_orders)
    st.markdown(
        f"<div style='text-align:center'>"
        f"<div style='font-size:.68rem;color:#666;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px'>Pending Orders</div>"
        f"<div style='font-size:1.6rem;font-weight:800;color:#f5c842'>{pending_count}</div>"
        f"<div style='font-size:.8rem;color:#e8a020;font-weight:600'>₹ {pending_total:,} unpaid</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:.68rem;color:#444;text-align:center;margin:0'>GF-27, Migsun Twiinz<br>Sector – Eta-2, Greater Noida</p>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# APP HEADER
# ══════════════════════════════════════════════════════════════════════════════
gs_badge = (
    "<span class='badge badge-green'>● Google Sheets connected</span>"
    if ws is not None else
    "<span class='badge badge-red'>● Google Sheets offline</span>"
)
st.markdown(f"""
<div class='app-header'>
    <div>
        <h1>Upsarpanch ChaiFi ☕</h1>
        <p>Shop No – GF-27, Migsun Twiinz, Sector – Eta-2, Greater Noida</p>
    </div>
    <div>{gs_badge}</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_new, tab_pending, tab_sales = st.tabs([
    "🛒  New Order",
    f"⏳  Pending Orders  ({len(st.session_state.pending_orders)})",
    "📊  Sales Dashboard",
])

# ════════════════════════ TAB 1 — NEW ORDER ══════════════════════════════════
with tab_new:
    col_order, col_bill = st.columns([1.1, 1], gap="large")

    # ── Left: build order ─────────────────────────────────────────────────────
    with col_order:
        st.markdown("<div class='section-title'>Current Cart</div>", unsafe_allow_html=True)

        if not st.session_state.cart:
            st.markdown("""
            <div class='empty-state'>
                <div class='icon'>🛒</div>
                <p>Cart is empty.<br>Pick items from the sidebar.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            to_remove = []
            for idx, (name, qty) in enumerate(st.session_state.cart.items()):
                price   = ALL_ITEMS[name]
                row_tot = price * qty
                c1, c2, c3, c4 = st.columns([4, 1.2, 1.2, 0.6])
                c1.markdown(
                    f"<div style='padding:8px 0'>"
                    f"<div style='font-size:.86rem;font-weight:500'>{name.split('⭐')[0].split('🆕')[0].strip()}</div>"
                    f"<div style='font-size:.72rem;color:#666'>₹ {price} each</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                new_qty = c2.number_input("qty", min_value=0, max_value=50, value=qty,
                                          key=f"q{idx}", label_visibility="collapsed")
                if new_qty != qty:
                    if new_qty == 0: to_remove.append(name)
                    else: st.session_state.cart[name] = new_qty
                    st.rerun()
                c3.markdown(
                    f"<div style='padding:8px 0;text-align:right;font-weight:700;color:#f5c842'>₹ {row_tot}</div>",
                    unsafe_allow_html=True,
                )
                if c4.button("✕", key=f"d{idx}"):
                    to_remove.append(name)
                st.markdown("<hr style='margin:2px 0'>", unsafe_allow_html=True)

            for n in to_remove: st.session_state.cart.pop(n, None)
            if to_remove: st.rerun()

            subtotal, discount_amt, total = calc_totals(st.session_state.cart)
            st.markdown(f"""
            <div class='totals-strip'>
                <div class='totals-row'><span class='t-label'>Subtotal</span><span class='t-val'>₹ {subtotal}</span></div>
                <div class='totals-row'>
                    <span class='t-label'>Discount (10%)</span>
                    <span class='t-val' style='color:{"#5dc95d" if discount_amt else "#444"}'>{"− ₹ "+str(discount_amt) if discount_amt else "—"}</span>
                </div>
                <div class='totals-row grand'><span>Total Payable</span><span class='t-val' style='color:#f5c842'>₹ {total}</span></div>
            </div>
            """, unsafe_allow_html=True)

            if subtotal < DISCOUNT_THRESHOLD:
                st.markdown(
                    f"<div class='nudge'>🏷️ Add ₹ {DISCOUNT_THRESHOLD - subtotal} more to unlock 10% off!</div>",
                    unsafe_allow_html=True,
                )

    # ── Right: generate bill & place order ────────────────────────────────────
    with col_bill:
        st.markdown("<div class='section-title'>Order Details</div>", unsafe_allow_html=True)

        customer = st.text_input("Customer Name", placeholder="Walk-in customer")
        token    = st.text_input("Table / Token No.", placeholder="e.g. T-3, Counter, Table-1")

        if st.session_state.cart:
            subtotal, discount_amt, total = calc_totals(st.session_state.cart)
            now     = datetime.now()
            bill_no = st.session_state.bill_counter

            preview_order = {
                "bill_no":   bill_no,
                "timestamp": now,
                "items":     dict(st.session_state.cart),
                "subtotal":  subtotal,
                "discount":  discount_amt,
                "total":     total,
                "customer":  customer.strip() or "Walk-in",
                "token":     token.strip() or "—",
            }
            bill_text = make_bill_text(preview_order)

            st.markdown(
                f"<div class='bill-receipt'><pre>{bill_text}</pre></div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            # ── Place Order button ──────────────────────────────────────────
            st.markdown(
                "<p style='font-size:.75rem;color:#666;margin-bottom:6px'>"
                "Customer will pay later. Click below to send to the Pending Orders queue.</p>",
                unsafe_allow_html=True,
            )
            if st.button("📋  Place Order → Pending", use_container_width=True):
                new_order = {
                    "id":        random.randint(100000, 999999),
                    "bill_no":   bill_no,
                    "timestamp": now,
                    "items":     dict(st.session_state.cart),
                    "subtotal":  subtotal,
                    "discount":  discount_amt,
                    "total":     total,
                    "customer":  customer.strip() or "Walk-in",
                    "token":     token.strip() or "—",
                }
                st.session_state.pending_orders.append(new_order)
                st.session_state.cart = {}
                st.session_state.bill_counter += 1
                st.success(f"✅ Order #{bill_no} placed! Go to ⏳ Pending Orders to mark as paid.")
                st.rerun()
        else:
            st.markdown("""
            <div class='empty-state'>
                <div class='icon'>🧾</div>
                <p>Bill preview will appear<br>once you add items.</p>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════ TAB 2 — PENDING ORDERS ══════════════════════════════
with tab_pending:
    pending = st.session_state.pending_orders

    if not pending:
        st.markdown("""
        <div class='empty-state' style='padding:4rem'>
            <div class='icon'>✅</div>
            <p style='font-size:1rem;font-weight:600;color:#5dc95d'>All clear!</p>
            <p style='margin-top:6px'>No pending orders. All bills have been paid.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Live summary bar
        total_pending_amt = sum(o["total"] for o in pending)
        st.markdown(f"""
        <div class='live-counter'>
            <div>
                <div class='live-counter-label'>Orders waiting for payment</div>
                <div style='display:flex;align-items:baseline;gap:12px;margin-top:4px'>
                    <div class='live-counter-value'>{len(pending)} orders</div>
                    <div class='live-counter-amount'>₹ {total_pending_amt:,} total unpaid</div>
                </div>
            </div>
            <div style='font-size:2rem;opacity:.4'>⏳</div>
        </div>
        """, unsafe_allow_html=True)

        to_mark_paid = []

        # Display each pending order
        for order in pending:
            items_lines = "".join(
                f"<div style='display:flex;justify-content:space-between'>"
                f"<span>{n.split('⭐')[0].split('🆕')[0].strip()} × {q}</span>"
                f"<span style='color:#666'>₹ {ALL_ITEMS[n]*q}</span>"
                f"</div>"
                for n, q in order["items"].items()
            )
            disc_html = (
                f"<div style='display:flex;justify-content:space-between;color:#5dc95d;font-size:.78rem'>"
                f"<span>Discount (10%)</span><span>− ₹ {order['discount']}</span></div>"
                if order["discount"] else ""
            )
            token_display = order["token"] if order["token"] != "—" else "—"

            st.markdown(f"""
            <div class='pending-card'>
                <div class='pending-card-header'>
                    <div>
                        <span class='pending-status-dot'></span>
                        <span class='pending-token'>#{order['bill_no']}
                            {"&nbsp;&nbsp;·&nbsp;&nbsp;" + token_display if token_display != "—" else ""}
                        </span>
                        &nbsp;&nbsp;
                        <span style='font-size:.75rem;color:#888'>{order['customer']}</span>
                    </div>
                    <span class='pending-time'>{order['timestamp'].strftime('%I:%M %p')}</span>
                </div>
                <div class='pending-card-body'>
                    <div class='pending-items-list'>
                        {items_lines}
                    </div>
                    <div style='border-top:1px solid #2a2a2a;padding-top:10px;margin-top:4px'>
                        {disc_html}
                        <div style='display:flex;justify-content:space-between;align-items:center;margin-top:4px'>
                            <span style='font-size:.75rem;color:#666'>TOTAL DUE</span>
                            <span class='pending-amount'>₹ {order['total']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons for each order
            bc1, bc2, bc3 = st.columns([2, 1.2, 1])

            with bc1:
                if st.button(f"✅  Mark as Paid  ·  ₹ {order['total']}", key=f"pay_{order['id']}", use_container_width=True):
                    to_mark_paid.append(order["id"])
                    # Save to Google Sheets
                    if ws is not None:
                        try:
                            append_bill_to_sheet(ws, order)
                            load_bills_from_sheet.clear()
                        except Exception as e:
                            st.error(f"Sheet save failed: {e}")

            with bc2:
                bill_txt = make_bill_text(order)
                st.download_button(
                    "⬇  Bill",
                    data=bill_txt,
                    file_name=f"ChaiFi_Bill_{order['bill_no']}.txt",
                    mime="text/plain",
                    key=f"dl_{order['id']}",
                    use_container_width=True,
                )

            with bc3:
                if st.button("🗑 Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                    to_mark_paid.append(order["id"])   # remove without saving

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Process paid / cancelled orders
        if to_mark_paid:
            st.session_state.pending_orders = [
                o for o in st.session_state.pending_orders if o["id"] not in to_mark_paid
            ]
            st.rerun()

# ════════════════════════ TAB 3 — SALES DASHBOARD ═════════════════════════════
with tab_sales:
    if ws is not None:
        all_bills = load_bills_from_sheet(ws)

    today       = date.today()
    week_start  = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    day_bills   = bills_in_range(all_bills, today,       today)
    week_bills  = bills_in_range(all_bills, week_start,  today)
    month_bills = bills_in_range(all_bills, month_start, today)

    day_rev,   day_cnt,   day_avg,   _ = sales_summary(day_bills)
    week_rev,  week_cnt,  week_avg,  _ = sales_summary(week_bills)
    month_rev, month_cnt, month_avg, _ = sales_summary(month_bills)

    st.markdown("<div class='section-title'>Revenue at a Glance</div>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3, gap="medium")
    for col, icon, label, rev, cnt, avg in [
        (k1, "📅", "Today",      day_rev,   day_cnt,   day_avg),
        (k2, "📆", "This Week",  week_rev,  week_cnt,  week_avg),
        (k3, "🗓️", "This Month", month_rev, month_cnt, month_avg),
    ]:
        col.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{icon} {label}</div>"
            f"<div class='kpi-value'>₹ {rev:,}</div>"
            f"<div class='kpi-sub'>{cnt} bills &nbsp;·&nbsp; avg ₹ {avg:.0f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    ch1, ch2 = st.columns(2, gap="medium")
    with ch1:
        period = st.selectbox("Period", ["Today","This Week","This Month"], key="period_sel")
        pmap   = {"Today": day_bills, "This Week": week_bills, "This Month": month_bills}
        _, _, _, top_items = sales_summary(pmap[period])
        max_q  = top_items[0][1] if top_items else 1
        st.markdown(
            f"<div class='chart-card'><div class='chart-card-title'>🏆 Top Selling Items — {period}</div>"
            + bar_chart_html(top_items, max_q) + "</div>",
            unsafe_allow_html=True,
        )

    with ch2:
        day_labels = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        day_revs   = [sum(b["total"] for b in bills_in_range(all_bills, d, d)) for d in day_labels]
        max_r      = max(day_revs) if any(day_revs) else 1
        rev_html   = "".join(
            f"<div class='bar-row'><div class='bar-name'>{d.strftime('%a %d')}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{(r/max_r*100) if max_r else 0:.1f}%'></div></div>"
            f"<div class='bar-num'>₹ {r:,}</div></div>"
            for d, r in zip(day_labels, day_revs)
        )
        st.markdown(
            "<div class='chart-card'><div class='chart-card-title'>📈 Daily Revenue — Last 7 Days</div>"
            + (rev_html if any(day_revs) else "<p style='color:#444;font-size:.8rem;padding:1rem 0'>No data yet.</p>")
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Bill History (Paid)</div>", unsafe_allow_html=True)

    hperiod = st.selectbox("Show", ["Today","This Week","This Month","All Time"], key="hist_sel")
    hmap    = {"Today": day_bills, "This Week": week_bills, "This Month": month_bills, "All Time": all_bills}
    hbills  = list(reversed(hmap[hperiod]))

    if not hbills:
        st.markdown("<div class='empty-state'><div class='icon'>📋</div><p>No paid bills in this period.</p></div>", unsafe_allow_html=True)
    else:
        for b in hbills:
            items_str = " · ".join(
                f"{n.split('⭐')[0].split('🆕')[0].strip()} ×{q}" for n, q in b["items"].items()
            )
            disc_str = f"&nbsp;<span class='discount-pill'>-₹{b['discount']}</span>" if b["discount"] else ""
            st.markdown(
                f"<div class='history-card'>"
                f"<div class='history-top'>"
                f"<span class='history-bill'>#{b['bill_no']}</span>"
                f"<span class='history-time'>{b['timestamp'].strftime('%d %b %Y · %I:%M %p')}</span>"
                f"</div>"
                f"<div class='history-items'>{items_str}</div>"
                f"<div class='history-bottom'>"
                f"<span class='history-customer'>👤 {b['customer']}</span>"
                f"<span class='history-total'>₹ {b['total']}{disc_str}</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    if ws is not None:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🔄  Refresh from Google Sheets"):
            load_bills_from_sheet.clear()
            st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:2rem 0 1rem;color:#333;font-size:.72rem;letter-spacing:.05em'>
    ☕ &nbsp; UPSARPANCH CHAIFI &nbsp; · &nbsp; I ❤️ Upsarpanch &nbsp; · &nbsp; 10% off on orders above ₹ 150
</div>
""", unsafe_allow_html=True)
