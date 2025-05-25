import streamlit as st
import pandas as pd
import numpy as np

# Configure page
st.set_page_config(page_title="Financial & Supply Chain Dashboard", layout="wide")
st.title("Interactive Inventory & Supply Chain Financial Dashboard")

# --- Sidebar Inputs ---
st.sidebar.header("User Inputs")
order_freq = st.sidebar.selectbox(
    "How often do you order?",
    ["Weekly", "Bi-weekly", "Monthly"],
    help="Select your ordering cadence"
)
budget = st.sidebar.number_input(
    "What’s your annual budget for inventory (€)?",
    min_value=0.0,
    value=100000.0,
    step=1000.0,
    format="%.2f"
)
demand_outlook = st.sidebar.selectbox(
    "Demand outlook",
    ["Pessimistic (-10%)", "Baseline (0%)", "Optimistic (+10%)"],
    help="Choose a simple demand scenario"
)

# --- Load Data ---
DATA_PATH = "/mnt/data/Transformation_Model_Suite (1).xlsx"
try:
    df = pd.read_excel(DATA_PATH)
    st.sidebar.success("Loaded financial dataset.")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Validate required columns
required_cols = [
    "Year", "Revenue", "COGS", "Current Assets", "Current Liabilities",
    "Inventory", "Cash", "Accounts Receivable", "Net Income", "Total Assets"
]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error(f"Missing columns in data: {missing}")
    st.stop()

# --- Historical CAGR to 2023 ---
hist = df[df["Year"] <= 2023].sort_values("Year")
start_year = int(hist.iloc[0]["Year"])
end_year = int(hist.iloc[-1]["Year"])
duration = end_year - start_year
cagr = {}
for col in required_cols:
    if col == "Year":
        continue
    start_val = hist.iloc[0][col]
    end_val = hist.iloc[-1][col]
    cagr[col] = (end_val / start_val) ** (1.0 / duration) - 1 if start_val > 0 else 0.0

# Project baseline to 2025
proj_year = 2025
years_forward = proj_year - end_year
base_proj = {col: hist.iloc[-1][col] * ((1 + cagr[col]) ** years_forward) for col in cagr}

# Apply demand outlook adjustment
outlook_factor = {
    "Pessimistic (-10%)": 0.9,
    "Baseline (0%)": 1.0,
    "Optimistic (+10%)": 1.1
}[demand_outlook]
adj_revenue = base_proj["Revenue"] * outlook_factor
adj_cogs = base_proj["COGS"] * outlook_factor

# Inventory adjustment
inv_base = base_proj["Inventory"]
adj_inventory = min(inv_base, budget)
freq_map = {"Weekly": 0.9, "Bi-weekly": 1.0, "Monthly": 1.1}
adj_inventory *= freq_map[order_freq]

# Recompute balance-sheet items
adj_ca = base_proj["Cash"] + base_proj["Accounts Receivable"] + adj_inventory
adj_cl = base_proj["Current Liabilities"]
adj_quick = adj_ca - adj_inventory
adj_wc = adj_ca - adj_cl
adj_ta = base_proj["Total Assets"]
adj_ni = base_proj["Net Income"] * (adj_revenue / base_proj["Revenue"])

# Helper for ratios
def compute_ratios(ca, cl, inv, ni, rev, ta):
    cr = ca / cl if cl else np.nan
    qr = (ca - inv) / cl if cl else np.nan
    wcr = (ca - cl) / ta if ta else np.nan
    npm = ni / rev if rev else np.nan
    return cr, qr, wcr, npm

base_cr, base_qr, base_wcr, base_npm = compute_ratios(
    base_proj["Current Assets"], base_proj["Current Liabilities"], base_proj["Inventory"],
    base_proj["Net Income"], base_proj["Revenue"], base_proj["Total Assets"]
)
adj_cr, adj_qr, adj_wcr, adj_npm = compute_ratios(
    adj_ca, adj_cl, adj_inventory, adj_ni, adj_revenue, adj_ta
)

# Display 2025 metrics
st.header("2025 Forecast: Base vs Adjusted")
metrics_df = pd.DataFrame([
    ("Revenue", base_proj["Revenue"], adj_revenue),
    ("COGS", base_proj["COGS"], adj_cogs),
    ("Inventory", base_proj["Inventory"], adj_inventory),
    ("Current Assets", base_proj["Current Assets"], adj_ca),
    ("Current Liabilities", base_proj["Current Liabilities"], adj_cl),
    ("Working Capital", base_proj["Current Assets"] - base_proj["Current Liabilities"], adj_wc),
    ("Quick Assets", base_proj["Current Assets"] - base_proj["Inventory"], adj_quick),
    ("Total Assets", base_proj["Total Assets"], adj_ta),
    ("Net Income", base_proj["Net Income"], adj_ni)
], columns=["Metric", "Base", "Adjusted"]).set_index("Metric")
st.dataframe(metrics_df.style.format("{:.2f}"))

# Display ratios
ratios_df = pd.DataFrame([
    ("Current Ratio", base_cr, adj_cr),
    ("Quick Ratio", base_qr, adj_qr),
    ("Working Capital Ratio", base_wcr, adj_wcr),
    ("Net Profit Margin", base_npm, adj_npm)
], columns=["Ratio", "Base", "Adjusted"]).set_index("Ratio")
st.subheader("Key Financial Ratios")
st.table(ratios_df.style.format("{:.2f}"))

# Assumptions & Explanations
st.markdown("---")
st.subheader("Assumptions & Explanations")
for item in [
    "Base 2025 via CAGR through 2023.",
    "Demand outlook: -10%/0%/+10%.",
    "Inventory budget cap and freq adj: Weekly=-10%, Bi-weekly=0%, Monthly=+10%."
]:
    st.markdown(f"- {item}")

assumptions_text = (
    "**What do changes in ratios mean?**\n"
    "- Current Ratio: higher ⇒ more liquidity; lower ⇒ potential strain.\n"
    "- Quick Ratio: higher ⇒ meet immediate obligations; lower ⇒ risk if inventory illiquid.\n"
    "- Working Capital Ratio: higher ⇒ buffer; lower ⇒ tight operations.\n"
    "- Net Profit Margin: higher ⇒ efficiency; lower ⇒ margin pressure."
)
st.markdown(assumptions_text)
