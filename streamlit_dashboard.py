import streamlit as st
import pandas as pd
import numpy as np

# ==============================
# Editable Baseline Values
# ==============================
# Update these fixed 2025 projections if needed
baseline = {
    'Revenue': 2245891597.48,
    'COGS': 753400000.00,
    'Current Assets': 1380508243.96,
    'Current Liabilities': 776610441.78,
    'Inventory': 418161077.55,
    'Cash': 229873783.64,
    'Accounts Receivable': 650803975.71,
    'Net Income': 43895489.22,
    'Total Assets': 2255221580.02
}

# Page configuration
st.set_page_config(page_title="Financial & Supply Chain Dashboard", layout="wide")
st.title("Interactive Inventory & Supply Chain Financial Dashboard")

# --- Sidebar Inputs & Scenario Descriptions ---
st.sidebar.header("User Inputs & Scenarios")
order_freq = st.sidebar.selectbox(
    "How often do you order?",
    ["Weekly", "Bi-weekly", "Monthly"],
    help="Reorder frequency: weekly replenishment lowers inventory; monthly increases it."
)
budget = st.sidebar.number_input(
    "What’s your annual budget for inventory (€)?",
    min_value=0.0,
    value=100000.0,
    step=1000.0,
    format="%.2f",
    help="Limits total inventory spend, controlling working capital tied up in stock."
)
demand_outlook = st.sidebar.selectbox(
    "Demand outlook",
    ["Pessimistic (-10%)", "Baseline (0%)", "Optimistic (+10%)"],
    help="Market scenario: scales Revenue & COGS by ±10%."
)

# Scenario explanations
st.subheader("What-If Scenario Descriptions")
st.markdown(
    """
**How often do you order?**  
- Weekly: frequent replenishment reduces average inventory (~-10%).  
- Bi-weekly: standard replenishment, neutral effect.  
- Monthly: less frequent replenishment increases inventory (~+10%).
"""
)
st.markdown(
    """
**Annual budget for inventory:**  
Sets the maximum amount you can invest in inventory, capping stock levels.
"""
)
st.markdown(
    """
**Demand outlook:**  
- Pessimistic (-10%): conservative forecast reduces sales and COGS.  
- Baseline (0%): neutral, no change.  
- Optimistic (+10%): growth forecast increases sales and COGS.
"""
)

# --- Apply user adjustments ---
out_map = {"Pessimistic (-10%)": 0.9, "Baseline (0%)": 1.0, "Optimistic (+10%)": 1.1}
adj_revenue = baseline['Revenue'] * out_map[demand_outlook]
adj_cogs    = baseline['COGS']    * out_map[demand_outlook]

inv_base = baseline['Inventory']
adj_inventory = min(inv_base, budget) * {'Weekly':0.9, 'Bi-weekly':1.0, 'Monthly':1.1}[order_freq]

# --- Recompute balance-sheet items ---
adj_ca    = baseline['Cash'] + baseline['Accounts Receivable'] + adj_inventory
adj_cl    = baseline['Current Liabilities']
adj_quick = adj_ca - adj_inventory
adj_wc    = adj_ca - adj_cl
adj_ta    = baseline['Total Assets']
adj_ni    = baseline['Net Income'] * (adj_revenue / baseline['Revenue'])

# --- Ratio computations ---
def compute_ratios(ca, cl, inv, ni, rev, ta):
    cr  = ca / cl if cl else np.nan
    qr  = (ca - inv) / cl if cl else np.nan
    wcr = (ca - cl) / ta if ta else np.nan
    npm = ni / rev if rev else np.nan
    return cr, qr, wcr, npm

base_cr, base_qr, base_wcr, base_npm = compute_ratios(
    baseline['Current Assets'], baseline['Current Liabilities'], baseline['Inventory'],
    baseline['Net Income'], baseline['Revenue'], baseline['Total Assets']
)
adj_cr, adj_qr, adj_wcr, adj_npm = compute_ratios(
    adj_ca, adj_cl, adj_inventory, adj_ni, adj_revenue, adj_ta
)

# --- Display Baseline vs Adjusted Metrics ---
st.header("2025 Forecast: Baseline vs Adjusted")
metrics = [
    ("Revenue", baseline['Revenue'], adj_revenue),
    ("COGS", baseline['COGS'], adj_cogs),
    ("Inventory", baseline['Inventory'], adj_inventory),
    ("Current Assets", baseline['Current Assets'], adj_ca),
    ("Current Liabilities", baseline['Current Liabilities'], adj_cl),
    ("Working Capital", baseline['Current Assets'] - baseline['Current Liabilities'], adj_wc),
    ("Quick Assets", baseline['Current Assets'] - baseline['Inventory'], adj_quick),
    ("Total Assets", baseline['Total Assets'], adj_ta),
    ("Net Income", baseline['Net Income'], adj_ni)
]
metrics_df = pd.DataFrame(metrics, columns=["Metric","Baseline","Adjusted"]).set_index("Metric")
st.dataframe(metrics_df.style.format("{:.2f}"))

# --- Display Key Financial Ratios ---
st.subheader("Key Financial Ratios")
ratios_df = pd.DataFrame([
    ("Current Ratio",       base_cr,  adj_cr),
    ("Quick Ratio",         base_qr,  adj_qr),
    ("Working Capital Ratio", base_wcr, adj_wcr),
    ("Net Profit Margin",   base_npm, adj_npm)
], columns=["Ratio","Baseline","Adjusted"]).set_index("Ratio")
st.table(ratios_df.style.format("{:.2f}"))

# --- Explanations for Ratios ---
st.markdown("---")
st.subheader("What Changes in These Ratios Mean")
st.markdown(
    "**Current Ratio:**  ↑ more liquidity buffer; ↓ tighter short-term debt coverage."
)
st.markdown(
    "**Quick Ratio:**    ↑ stronger immediate liquidity; ↓ more reliance on inventory."
)
st.markdown(
    "**Working Capital Ratio:**  ↑ greater operational cushion; ↓ potential cash flow strain."
)
st.markdown(
    "**Net Profit Margin:**  ↑ higher profitability per € revenue; ↓ increased cost pressure."
)
