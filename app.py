import streamlit as st
from datetime import datetime, date, timedelta
import random
import json
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Upsarpanch ChaiFi – Billing & Sales",
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
SHEET_NAME         = "ChaiFi_Bills"   # name of the Google Sheet
WORKSHEET_NAME     = "Bills"          # tab inside the sheet

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&display=swap');

.stApp { background: #1a0f00; color: #f5e6c8; }
[data-testid="stSidebar"] { background: #2d1a00 !important; border-right: 2px solid #c8860a; }
[data-testid="stSidebar"] * { color: #f5e6c8 !important; }
h1,h2,h3 { font-family:'Playfair Display',serif; color:#f5c842 !important; }
input[type="number"] { background:#2d1a00 !important; color:#f5e6c8 !important; border:1px solid #c8860a !important; border-radius:6px !important; }
.stButton>button { background:linear-gradient(135deg,#c8860a,#f5c842); color:#1a0f00 !important; font-weight:700; border:none; border-radius:8px; padding:.5rem 1.5rem; font-size:1rem; cursor:pointer; transition:opacity .2s; }
.stButton>button:hover { opacity:.85; }
hr { border-color:#c8860a44 !important; }
[data-testid="stMetricValue"] { color:#f5c842 !important; font-size:1.5rem !important; }
[data-testid="stMetricLabel"] { color:#c8a060 !important; }
.bill-box { background:#fdf6e3; color:#1a0f00; border-radius:12px; padding:24px 28px; font-family:'Courier New',monospace; font-size:.9rem; line-height:1.8; border:2px solid #c8860a; box-shadow:0 4px 24px #0007; }
.stSelectbox label,.stNumberInput label,.stTextInput label { color:#c8a060 !important; font-size:.85rem; }
.stAlert { border-radius:8px !important; }
.sales-card { background:#2d1a00; border:1px solid #c8860a55; border-radius:12px; padding:18px 20px; margin-bottom:12px; }
.bill-row { background:#2d1a00; border-left:3px solid #c8860a; border-radius:0 8px 8px 0; padding:10px 14px; margin-bottom:8px; font-size:.85rem; }
.bar-wrap { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.bar-label { width:160px; font-size:.78rem; color:#c8a060; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar-bg { flex:1; background:#2d1a00; border-radius:4px; height:18px; }
.bar-fill { height:18px; border-radius:4px; background:linear-gradient(90deg,#c8860a,#f5c842); }
.bar-val { width:60px; text-align:right; font-size:.78rem; color:#f5e6c8; flex-shrink:0; }
.gs-badge { display:inline-flex; align-items:center; gap:6px; background:#1a3a1a; border:1px solid #2d8a2d; border-radius:20px; padding:3px 12px; font-size:.78rem; color:#5dc95d; }
.gs-badge-err { background:#3a1a1a; border-color:#8a2d2d; color:#c95d5d; }
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#1a0f00; }
::-webkit-scrollbar-thumb { background:#c8860a; border-radius:3px; }
button[data-baseweb="tab"] { color:#c8a060 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color:#f5c842 !important; border-bottom-color:#f5c842 !important; }
</style>
""", unsafe_allow_html=True)

# ── Google Sheets connection ──────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_HEADERS = [
    "Bill No", "Date", "Time", "Customer", "Token",
    "Items (JSON)", "Subtotal", "Discount", "Total"
]

@st.cache_resource(show_spinner=False)
def get_worksheet():
    """Return (worksheet, error_string). Cached so we reconnect only on cold start."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc    = gspread.authorize(creds)
        sh    = gc.open(SHEET_NAME)
        try:
            ws = sh.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=5000, cols=20)
            ws.append_row(SHEET_HEADERS)
        # Ensure header row exists
        existing = ws.row_values(1)
        if existing != SHEET_HEADERS:
            ws.insert_row(SHEET_HEADERS, 1)
        return ws, None
    except Exception as e:
        return None, str(e)


def append_bill_to_sheet(ws, bill: dict):
    """Write one bill row to the sheet."""
    ws.append_row([
        bill["bill_no"],
        bill["timestamp"].strftime("%Y-%m-%d"),
        bill["timestamp"].strftime("%H:%M:%S"),
        bill["customer"],
        bill["token"],
        json.dumps(bill["items"], ensure_ascii=False),
        bill["subtotal"],
        bill["discount"],
        bill["total"],
    ], value_input_option="USER_ENTERED")


@st.cache_data(ttl=30, show_spinner=False)
def load_bills_from_sheet(_ws) -> list:
    """
    Load all bill rows from the sheet and return list of bill dicts.
    Result is cached for 30 seconds to avoid hammering the API on every rerun.
    """
    records = _ws.get_all_records()   # list of dicts keyed by header row
    bills = []
    for r in records:
        try:
            items = json.loads(r["Items (JSON)"])
            dt    = datetime.strptime(
                f"{r['Date']} {r['Time']}", "%Y-%m-%d %H:%M:%S"
            )
            bills.append({
                "bill_no":   int(r["Bill No"]),
                "timestamp": dt,
                "items":     items,
                "subtotal":  int(r["Subtotal"]),
                "discount":  int(r["Discount"]),
                "total":     int(r["Total"]),
                "customer":  r["Customer"],
                "token":     r["Token"],
            })
        except Exception:
            continue   # skip malformed rows
    return bills


# ── Session state ─────────────────────────────────────────────────────────────
if "cart"          not in st.session_state: st.session_state.cart = {}
if "bill_counter"  not in st.session_state: st.session_state.bill_counter = None
if "gs_connected"  not in st.session_state: st.session_state.gs_connected = False

# ── Helpers ───────────────────────────────────────────────────────────────────
def all_items():
    out = {}
    for cat in MENU.values():
        out.update(cat)
    return out

ALL_ITEMS = all_items()

def calc_totals(cart):
    sub  = sum(ALL_ITEMS[n] * q for n, q in cart.items())
    disc = (sub * DISCOUNT_PCT // 100) if sub >= DISCOUNT_THRESHOLD else 0
    return sub, disc, sub - disc

def bills_in_range(bills, start: date, end: date):
    return [b for b in bills if start <= b["timestamp"].date() <= end]

def sales_summary(bill_list):
    rev   = sum(b["total"] for b in bill_list)
    cnt   = len(bill_list)
    avg   = rev / cnt if cnt else 0
    items = defaultdict(int)
    for b in bill_list:
        for name, qty in b["items"].items():
            items[name] += qty
    top = sorted(items.items(), key=lambda x: x[1], reverse=True)[:5]
    return rev, cnt, avg, top

def mini_bar_chart(items, max_qty):
    if not items:
        return "<p style='color:#c8a060;font-size:.8rem'>No data yet.</p>"
    html = ""
    for name, qty in items:
        pct   = (qty / max_qty * 100) if max_qty else 0
        label = name[:24]
        html += (
            f"<div class='bar-wrap'>"
            f"<div class='bar-label' title='{name}'>{label}</div>"
            f"<div class='bar-bg'><div class='bar-fill' style='width:{pct:.1f}%'></div></div>"
            f"<div class='bar-val'>{qty} pcs</div>"
            f"</div>"
        )
    return html

# ── Connect to Google Sheets ───────────────────────────────────────────────────
ws, gs_error = get_worksheet()

if ws is not None:
    # Load bills & derive next bill number
    all_bills = load_bills_from_sheet(ws)
    if st.session_state.bill_counter is None:
        max_no = max((b["bill_no"] for b in all_bills), default=1000)
        st.session_state.bill_counter = max_no + 1
else:
    all_bills = []
    if st.session_state.bill_counter is None:
        st.session_state.bill_counter = random.randint(1000, 1099)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# ☕ Upsarpanch ChaiFi")
st.markdown(
    "<p style='color:#c8a060;margin-top:-10px;'>Shop No – GF-27, Migsun Twiinz, Sector – Eta-2, Greater Noida</p>",
    unsafe_allow_html=True,
)

# Google Sheets status badge
if ws is not None:
    st.markdown(
        "<span class='gs-badge'>🟢 Google Sheets connected — bills are saved automatically</span>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"<span class='gs-badge gs-badge-err'>🔴 Google Sheets not connected — bills saved in session only &nbsp;|&nbsp; {gs_error}</span>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ☕ Add to Order")
    st.markdown("---")

    category = st.selectbox("Category", list(MENU.keys()))
    item     = st.selectbox("Item", list(MENU[category].keys()))
    price    = MENU[category][item]
    qty      = st.number_input("Qty", min_value=1, max_value=20, value=1, step=1)
    st.markdown(f"**Price:** ₹ {price} × {qty} = ₹ {price * qty}")

    if st.button("➕  Add to Bill", use_container_width=True):
        st.session_state.cart[item] = st.session_state.cart.get(item, 0) + qty
        st.success(f"Added {qty}× {item}")

    st.markdown("---")
    if st.button("🗑️  Clear Cart", use_container_width=True):
        st.session_state.cart = {}
        st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_billing, tab_sales = st.tabs(["🧾  Billing", "📊  Sales Dashboard"])

# ═════════════════════════ TAB 1 — BILLING ═══════════════════════════════════
with tab_billing:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown("### 🛒 Current Order")
        if not st.session_state.cart:
            st.info("No items added yet. Use the sidebar to add items.")
        else:
            to_remove = []
            for idx, (name, qty) in enumerate(st.session_state.cart.items()):
                price   = ALL_ITEMS[name]
                row_tot = price * qty
                cols    = st.columns([3.5, 1.2, 1.2, 1.2, 0.6])
                cols[0].markdown(f"<span style='font-size:.9rem'>{name}</span>", unsafe_allow_html=True)
                cols[1].markdown(f"<span style='color:#c8a060'>₹{price}</span>", unsafe_allow_html=True)
                new_qty = cols[2].number_input("qty", min_value=0, max_value=50, value=qty,
                                               key=f"qty_{idx}", label_visibility="collapsed")
                if new_qty != qty:
                    if new_qty == 0: to_remove.append(name)
                    else: st.session_state.cart[name] = new_qty
                    st.rerun()
                cols[3].markdown(f"**₹ {row_tot}**")
                if cols[4].button("✕", key=f"del_{idx}"):
                    to_remove.append(name)

            for name in to_remove:
                st.session_state.cart.pop(name, None)
            if to_remove:
                st.rerun()

            st.markdown("---")
            subtotal, discount_amt, total = calc_totals(st.session_state.cart)
            m1, m2, m3 = st.columns(3)
            m1.metric("Subtotal",              f"₹ {subtotal}")
            m2.metric(f"Discount ({DISCOUNT_PCT}%)", f"– ₹ {discount_amt}")
            m3.metric("Total",                 f"₹ {total}")
            if subtotal < DISCOUNT_THRESHOLD:
                st.markdown(
                    f"<p style='color:#c8a060;font-size:.8rem'>Add ₹ {DISCOUNT_THRESHOLD-subtotal} more to unlock 10% off!</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.success(f"🎉 You saved ₹ {discount_amt} with the 10% offer!")

    with right:
        st.markdown("### 🧾 Bill Preview")
        customer = st.text_input("Customer name (optional)", placeholder="Walk-in")
        token    = st.text_input("Table / Token no. (optional)", placeholder="—")

        if st.session_state.cart:
            subtotal, discount_amt, total = calc_totals(st.session_state.cart)
            now     = datetime.now()
            bill_no = st.session_state.bill_counter

            lines = [
                f"{'Upsarpanch ChaiFi':^42}",
                f"{'The CHAI FI Caffe':^42}",
                f"{'GF-27, Migsun Twiinz, Eta-2':^42}",
                f"{'Greater Noida':^42}",
                "─" * 42,
                f"Bill No : #{bill_no}",
                f"Date    : {now.strftime('%d %b %Y  %I:%M %p')}",
            ]
            if customer.strip(): lines.append(f"Customer: {customer.strip()}")
            if token.strip():    lines.append(f"Token   : {token.strip()}")
            lines += [
                "─" * 42,
                f"{'ITEM':<24} {'QTY':>3}  {'AMT':>7}",
                "─" * 42,
            ]
            for name, qty in st.session_state.cart.items():
                p   = ALL_ITEMS[name]
                rt  = p * qty
                disp = name[:22] if len(name) > 22 else name
                lines.append(f"{disp:<24} {qty:>3}  ₹{rt:>5}")
            lines.append("─" * 42)
            lines.append(f"{'Subtotal':<30} ₹{subtotal:>5}")
            if discount_amt:
                lines.append(f"{'Discount (10% off ₹150+)':<30} -₹{discount_amt:>4}")
                lines.append("─" * 42)
            lines += [
                f"{'TOTAL':<30} ₹{total:>5}",
                "─" * 42,
                f"{'Thank you! Ek Chai Ho Jaye? ☕':^42}",
                f"{'Warm Moments, Great Flavors':^42}",
            ]
            bill_text = "\n".join(lines)

            st.markdown(
                f"<div class='bill-box'><pre style='margin:0;font-family:Courier New,monospace;"
                f"font-size:.82rem;background:transparent;color:#1a0f00'>{bill_text}</pre></div>",
                unsafe_allow_html=True,
            )
            st.markdown("")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅  Confirm & New Bill", use_container_width=True):
                    bill_record = {
                        "bill_no":   bill_no,
                        "timestamp": now,
                        "items":     dict(st.session_state.cart),
                        "subtotal":  subtotal,
                        "discount":  discount_amt,
                        "total":     total,
                        "customer":  customer.strip() or "Walk-in",
                        "token":     token.strip() or "—",
                    }
                    # ── Save to Google Sheets ──────────────────────────────────
                    if ws is not None:
                        try:
                            append_bill_to_sheet(ws, bill_record)
                            load_bills_from_sheet.clear()   # bust cache so dashboard refreshes
                            st.success("✅ Bill saved to Google Sheets!")
                        except Exception as e:
                            st.error(f"Sheet write failed: {e}")
                    else:
                        st.warning("Google Sheets not connected. Bill not persisted.")

                    st.session_state.cart = {}
                    st.session_state.bill_counter += 1
                    st.rerun()

            with col2:
                st.download_button(
                    label="⬇️  Save Bill (.txt)",
                    data=bill_text,
                    file_name=f"ChaiFi_Bill_{bill_no}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        else:
            st.markdown(
                "<div style='color:#c8a060;padding:20px 0'>Add items from the sidebar to generate a bill.</div>",
                unsafe_allow_html=True,
            )

# ═════════════════════════ TAB 2 — SALES DASHBOARD ═══════════════════════════
with tab_sales:
    st.markdown("### 📊 Sales Dashboard")

    # Reload from Sheets every time the tab is viewed (cache TTL handles throttle)
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

    # ── KPI cards ─────────────────────────────────────────────────────────────
    st.markdown("#### Revenue at a Glance")
    c1, c2, c3 = st.columns(3)
    for col, label, rev, cnt, avg in [
        (c1, "📅 TODAY",      day_rev,   day_cnt,   day_avg),
        (c2, "📆 THIS WEEK",  week_rev,  week_cnt,  week_avg),
        (c3, "🗓️ THIS MONTH", month_rev, month_cnt, month_avg),
    ]:
        col.markdown(
            f"<div class='sales-card'>"
            f"<p style='color:#c8a060;font-size:.8rem;margin:0'>{label}</p>"
            f"<h2 style='margin:4px 0;color:#f5c842'>₹ {rev:,}</h2>"
            f"<p style='font-size:.82rem;color:#f5e6c8;margin:0'>{cnt} bills &nbsp;·&nbsp; avg ₹ {avg:.0f}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Charts row ────────────────────────────────────────────────────────────
    left2, right2 = st.columns(2, gap="large")

    with left2:
        period_label = st.selectbox("Top items for", ["Today", "This Week", "This Month"], key="top_period")
        pmap = {"Today": day_bills, "This Week": week_bills, "This Month": month_bills}
        _, _, _, top_items = sales_summary(pmap[period_label])
        max_qty = top_items[0][1] if top_items else 1
        st.markdown(f"#### 🏆 Top Selling Items — {period_label}")
        st.markdown(mini_bar_chart(top_items, max_qty), unsafe_allow_html=True)
        if not top_items:
            st.info("No bills yet. Confirm a bill to see data here.")

    with right2:
        st.markdown("#### 📈 Daily Revenue — Last 7 Days")
        day_labels = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        day_revs   = [sum(b["total"] for b in bills_in_range(all_bills, d, d)) for d in day_labels]
        max_rev    = max(day_revs) if any(day_revs) else 1
        chart_html = ""
        for d, rev in zip(day_labels, day_revs):
            pct = (rev / max_rev * 100) if max_rev else 0
            chart_html += (
                f"<div class='bar-wrap'>"
                f"<div class='bar-label'>{d.strftime('%a %d')}</div>"
                f"<div class='bar-bg'><div class='bar-fill' style='width:{pct:.1f}%'></div></div>"
                f"<div class='bar-val'>₹ {rev:,}</div>"
                f"</div>"
            )
        st.markdown(
            chart_html if any(day_revs) else "<p style='color:#c8a060;font-size:.8rem'>No data yet.</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Bill history ──────────────────────────────────────────────────────────
    st.markdown("#### 🗂️ Bill History")
    hist_period = st.selectbox(
        "Show bills from", ["Today", "This Week", "This Month", "All Time"], key="hist_period"
    )
    hmap = {
        "Today":      day_bills,
        "This Week":  week_bills,
        "This Month": month_bills,
        "All Time":   all_bills,
    }
    hist_bills = list(reversed(hmap[hist_period]))

    if not hist_bills:
        st.info("No bills in this period yet.")
    else:
        for b in hist_bills:
            items_str    = ", ".join(
                f"{n.split('⭐')[0].split('🆕')[0].strip()} ×{q}" for n, q in b["items"].items()
            )
            discount_str = f"  |  Discount –₹{b['discount']}" if b["discount"] else ""
            st.markdown(
                f"<div class='bill-row'>"
                f"<b style='color:#f5c842'>#{b['bill_no']}</b>"
                f"&nbsp; <span style='color:#c8a060'>{b['timestamp'].strftime('%d %b %Y %I:%M %p')}</span>"
                f"&nbsp;·&nbsp; {b['customer']}"
                f"<br/><span style='color:#f5e6c8'>{items_str}</span>"
                f"<br/><span style='color:#c8a060;font-size:.8rem'>Subtotal ₹{b['subtotal']}{discount_str}</span>"
                f"&nbsp; <b style='color:#f5c842'>Total ₹{b['total']}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Refresh button ────────────────────────────────────────────────────────
    if ws is not None:
        st.markdown("")
        if st.button("🔄  Refresh from Google Sheets"):
            load_bills_from_sheet.clear()
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#c8a060;font-size:.78rem'>"
    "Upsarpanch ChaiFi &nbsp;|&nbsp; I ❤️ Upsarpanch &nbsp;|&nbsp; "
    "10% off on orders above ₹ 150"
    "</p>",
    unsafe_allow_html=True,
)
