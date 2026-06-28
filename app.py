import streamlit as st
from datetime import datetime, date, timedelta
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
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; }
.stApp { background: #f5f5f0; color: #1a1a1a; font-family: 'Sora', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* hide sidebar entirely */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

.block-container { padding: 0 2rem 2rem 2rem !important; max-width: 1400px; }

/* ── Inputs ── */
input, textarea, div[data-baseweb="input"] input {
    background: #fff !important; color: #1a1a1a !important;
    border-color: #e0ddd8 !important; border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important;
}
.stSelectbox > div > div {
    background: #fff !important; border-color: #e0ddd8 !important;
    border-radius: 10px !important; color: #1a1a1a !important;
}
input[type="number"] {
    background: #fff !important; color: #1a1a1a !important;
    border: 1px solid #e0ddd8 !important; border-radius: 10px !important;
}
label, .stSelectbox label, .stNumberInput label, .stTextInput label {
    color: #999 !important; font-size: 0.72rem !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.07em;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #b8720a, #e8a020, #f5c842) !important;
    color: #fff !important; font-weight: 700 !important;
    font-family: 'Sora', sans-serif !important; border: none !important;
    border-radius: 10px !important; padding: 0.55rem 1.2rem !important;
    font-size: 0.88rem !important; transition: all 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(184,114,10,.2) !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(184,114,10,.35) !important; }

.stDownloadButton > button {
    background: #fff !important; color: #b8720a !important;
    border: 1.5px solid #b8720a !important; border-radius: 10px !important;
    font-weight: 600 !important; font-family: 'Sora', sans-serif !important;
    font-size: 0.85rem !important; transition: all 0.2s !important;
}
.stDownloadButton > button:hover { background: #b8720a !important; color: #fff !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    background: #fff; border-radius: 12px; padding: 4px;
    border: 1px solid #e8e4dc; gap: 4px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
button[data-baseweb="tab"] {
    background: transparent !important; color: #aaa !important;
    border-radius: 8px !important; font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important; font-size: 0.85rem !important;
    padding: 0.5rem 1.2rem !important; transition: all 0.2s !important; border: none !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #b8720a, #e8a020) !important; color: #fff !important;
}
[data-testid="stTabs"] [role="tabpanel"] { padding-top: 1.5rem; }

/* ── Misc ── */
hr { border: none !important; border-top: 1px solid #e8e4dc !important; margin: 1rem 0 !important; }
.stAlert { border-radius: 10px !important; font-family: 'Sora', sans-serif !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #f0ede8; }
::-webkit-scrollbar-thumb { background: #d4cfc8; border-radius: 2px; }

/* ── App header ── */
.app-header {
    background: #fff; border-bottom: 1px solid #e8e4dc;
    padding: 1.1rem 2rem; margin: 0 -2rem 1.5rem -2rem;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 0.8rem; box-shadow: 0 1px 6px rgba(0,0,0,.05);
}
.app-header h1 { font-size: 1.4rem !important; font-weight: 800 !important; color: #b8720a !important; margin: 0 !important; }
.app-header p  { font-size: 0.72rem; color: #aaa; margin: 2px 0 0; }

/* ── Badges ── */
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-green { background: #edfaed; border: 1px solid #4caf50; color: #2e7d32; }
.badge-red   { background: #fdecea; border: 1px solid #f44336; color: #c62828; }

/* ── Item picker panel ── */
.picker-panel {
    background: #fff;
    border: 1px solid #e8e4dc;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 6px rgba(0,0,0,.05);
}
.picker-title {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: #bbb; margin-bottom: 0.9rem;
}

/* ── Section title ── */
.section-title { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #bbb; margin-bottom: 0.8rem; }

/* ── Totals strip ── */
.totals-strip { background: #fff; border: 1px solid #e8e4dc; border-radius: 14px; padding: 1rem 1.2rem; margin-top: 0.8rem; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.totals-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.85rem; }
.totals-row.grand { border-top: 1px solid #e8e4dc; margin-top: 8px; padding-top: 10px; font-size: 1.05rem; font-weight: 700; }
.totals-row .t-label { color: #aaa; }
.totals-row .t-val   { color: #1a1a1a; }
.nudge { background: #fff8ec; border: 1.5px dashed #e8a020; border-radius: 10px; padding: 10px 14px; font-size: 0.8rem; color: #b8720a; margin-top: 8px; text-align: center; font-weight: 500; }

/* ── Bill receipt ── */
.bill-receipt {
    background: #fffdf7; border-radius: 14px; padding: 26px 30px;
    border: 1px solid #e8d8b0; box-shadow: 0 4px 20px rgba(184,114,10,.08);
    font-family: 'JetBrains Mono', monospace; color: #1a1200;
    position: relative; overflow: hidden;
}
.bill-receipt::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #b8720a, #e8a020, #f5c842, #e8a020, #b8720a);
}
.bill-receipt pre { margin: 0; font-size: 0.77rem; line-height: 1.9; background: transparent; color: #1a1200; white-space: pre; font-family: 'JetBrains Mono', monospace; }

/* ── KPI card ── */
.kpi-card { background: #fff; border: 1px solid #e8e4dc; border-radius: 16px; padding: 1.2rem 1.4rem; transition: border-color 0.2s, box-shadow 0.2s; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.kpi-card:hover { border-color: #e8a020; box-shadow: 0 4px 16px rgba(184,114,10,.12); }
.kpi-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #bbb; margin-bottom: 6px; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: #b8720a; line-height: 1; margin-bottom: 4px; }
.kpi-sub   { font-size: 0.75rem; color: #aaa; }

/* ── Chart ── */
.bar-row   { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.bar-name  { font-size: 0.75rem; color: #aaa; width: 150px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; background: #f0ede8; border-radius: 6px; height: 18px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #b8720a, #f5c842); }
.bar-num   { font-size: 0.75rem; color: #555; font-weight: 600; width: 55px; text-align: right; flex-shrink: 0; }
.chart-card { background: #fff; border: 1px solid #e8e4dc; border-radius: 16px; padding: 1.2rem 1.4rem; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.chart-card-title { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #bbb; margin-bottom: 1rem; }

/* ── History card ── */
.history-card { background: #fff; border: 1px solid #e8e4dc; border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.history-top  { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.history-bill { font-size: 0.8rem; font-weight: 700; color: #b8720a; font-family: 'JetBrains Mono', monospace; }
.history-time { font-size: 0.72rem; color: #bbb; }
.history-items { font-size: 0.78rem; color: #888; margin-bottom: 6px; line-height: 1.5; }
.history-bottom { display: flex; justify-content: space-between; align-items: center; }
.history-customer { font-size: 0.72rem; color: #bbb; }
.history-total { font-size: 0.88rem; font-weight: 700; color: #b8720a; }
.discount-pill { background: #edfaed; border: 1px solid #4caf50; color: #2e7d32; border-radius: 20px; padding: 2px 10px; font-size: 0.72rem; font-weight: 600; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 2.5rem 2rem; }
.empty-state .icon { font-size: 2.5rem; margin-bottom: 0.8rem; opacity: 0.3; }
.empty-state p { font-size: 0.85rem; margin: 0; color: #bbb; }

/* ── Pending cards ── */
.pending-card {
    background: #fff; border: 1.5px solid #e8e4dc; border-radius: 16px;
    margin-bottom: 14px; overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,.05); transition: box-shadow 0.2s;
}
.pending-card:hover { box-shadow: 0 4px 20px rgba(184,114,10,.12); border-color: #e8a020; }
.pending-card-header {
    background: #fffbf4; padding: 12px 18px;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid #f0e8d8;
}
.pending-token { font-size: 1rem; font-weight: 800; color: #b8720a; font-family: 'JetBrains Mono', monospace; }
.pending-time  { font-size: 0.72rem; color: #bbb; background: #f5f2ec; padding: 3px 10px; border-radius: 20px; }
.pending-status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #e8a020; margin-right: 8px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.3; } }

/* ── Live counter ── */
.live-counter {
    background: #fff8ec; border: 1.5px solid #f5c842; border-radius: 14px;
    padding: 16px 22px; display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 1.4rem;
    box-shadow: 0 2px 10px rgba(184,114,10,.08);
}
.live-counter-label  { font-size: 0.7rem; color: #b8720a; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; margin-bottom: 4px; }
.live-counter-value  { font-size: 1.6rem; font-weight: 800; color: #b8720a; display: inline; }
.live-counter-amount { font-size: 0.9rem; color: #e8a020; font-weight: 600; margin-left: 12px; }
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
    lines += ["─"*44, f"  {'ITEM':<24}{'QTY':>5}  {'AMT':>8}", "─"*44]
    for name, qty in order["items"].items():
        rt   = ALL_ITEMS[name] * qty
        disp = clean(name)[:22]
        lines.append(f"  {disp:<24}{qty:>5}  ₹{rt:>6}")
    lines += ["─"*44, f"  {'Subtotal':<30}₹{order['subtotal']:>8}"]
    if order["discount"]:
        lines.append(f"  {'Discount (10% off ₹150+)':<30}-₹{order['discount']:>7}")
    lines += ["═"*44, f"  {'TOTAL PAYABLE':<30}₹{order['total']:>8}", "═"*44,
              "", f"{'Ek Chai Ho Jaye? ☕':^44}", f"{'Thank you for visiting!':^44}"]
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
    "<span class='badge badge-green'>● Google Sheets connected</span>"
    if ws is not None else
    "<span class='badge badge-red'>● Google Sheets offline</span>"
)
st.markdown(
    f"<div class='app-header'>"
    f"<div><h1>Upsarpanch ChaiFi ☕</h1>"
    f"<p>Shop No – GF-27, Migsun Twiinz, Sector – Eta-2, Greater Noida</p></div>"
    f"<div>{gs_badge_html}</div>"
    f"</div>",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
pending_count = len(st.session_state.pending_orders)
tab_new, tab_pending, tab_sales = st.tabs([
    "🛒  New Order",
    f"⏳  Pending Orders  ({pending_count})",
    "📊  Sales Dashboard",
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
                    f"<div style='font-size:.86rem;font-weight:600;color:#1a1a1a'>{clean(name)}</div>"
                    f"<div style='font-size:.72rem;color:#bbb'>₹ {p} each</div></div>",
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
            now     = datetime.now()
            bill_no = st.session_state.bill_counter

            preview = {
                "bill_no": bill_no, "timestamp": now,
                "items": dict(st.session_state.cart),
                "subtotal": subtotal, "discount": discount_amt, "total": total,
                "customer": customer.strip() or "Walk-in",
                "token":    token.strip() or "—",
            }
            st.markdown(
                f"<div class='bill-receipt'><pre>{make_bill_text(preview)}</pre></div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='font-size:.73rem;color:#bbb;margin-bottom:6px'>"
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
                f"<span style='font-size:.78rem;color:#aaa;margin-left:4px'>{order['customer']}</span>"
                f"</div>"
                f"<span class='pending-time'>{order['timestamp'].strftime('%I:%M %p')}</span>"
                f"</div>"
                f"<div style='padding:16px 18px;display:flex;justify-content:space-between;align-items:center'>"
                f"<div style='font-size:.78rem;color:#bbb;max-width:60%'>{item_summary}</div>"
                f"<div style='text-align:right'>"
                f"<div style='font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:#bbb;font-weight:700'>Total Due</div>"
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
                        f"<div style='font-size:.84rem;font-weight:600'>{clean(iname)}</div>"
                        f"<div style='font-size:.7rem;color:#bbb'>₹ {iprice} each</div></div>",
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
                    "<div style='font-size:.68rem;color:#aaa;font-weight:600;margin-bottom:6px'>ADD ITEM</div>",
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

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;padding:2rem 0 1rem;color:#ccc;font-size:.72rem;letter-spacing:.05em'>"
    "☕ UPSARPANCH CHAIFI · I ❤️ Upsarpanch · 10% off on orders above ₹ 150"
    "</div>",
    unsafe_allow_html=True,
)
