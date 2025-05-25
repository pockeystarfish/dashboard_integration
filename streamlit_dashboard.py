import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Financial & Supply Chain Dashboard", layout="wide")
st.title("Interactive Inventory & Supply Chain Financial Dashboard")

# Sidebar inputs
st.sidebar.header("User Inputs")
order_freq = st.sidebar.selectbox(
    "How often do you order?",
    options=["Weekly", "Bi-weekly", "Monthly"],
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
    options=["Pessimistic (-10%)", "Baseline (0%)", "Optimistic (+10%)"],
    help="Choose a simple demand scenario"
)

# Load financial data from provided Excel file
DATA_PATH = '/mnt/data/Transformation_Model_Suite (1).xlsx'
try:
    df = pd.read_excel(DATA_PATH, sheet_name=0)
    st.sidebar.success("Dataset loaded successfully from provided file.")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Ensure expected columns exist in the uploaded data
required_cols = ["Year", "Revenue", "COGS", "Current Assets", "Current Liabilities",
                 "Inventory", "Cash", "Accounts Receivable", "Net Income", "Total Assets"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# Historical CAGR calculation up to 2023 using the uploaded Excel data
hist = df[df['Year'] <= 2023].copy()
start_year = hist['Year'].min()
end_year = hist['Year'].max()
yrs = end_year - start_year
cagr = {}
for col in required_cols[1:]:  # skip 'Year'
    start_val = hist.loc[hist['Year'] == start_year, col].values[0]
    end_val = hist.loc[hist['Year'] == end_year, col].values[0]
    cagr[col] = (end_val / start_val) ** (1/yrs) - 1 if start_val > 0 else 0.0

# Project base 2025 values derived directly from the Excel file projections
proj_year = 2025
years_to_proj = proj_year - end_year
base_proj = {
    col: df.loc[df['Year'] == end_year, col].values[0] * ((1 + gr) ** years_to_proj)
    for col, gr in cagr.items()
}

# Apply user adjustments on top of base 2025 projections
outlook_factor = {"Pessimistic (-10%)": 0.9, "Baseline (0%)": 1.0, "Optimistic (+10%)": 1.1}[demand_outlook]
adj_revenue = base_proj['Revenue'] * outlook_factor
adj_cogs = base_proj['COGS'] * outlook_factor

# Inventory budget cap and frequency effect
inv_base = base_proj['Inventory']
adj_inventory = min(inv_base, budget)
freq_map = {"Weekly": 0.9, "Bi-weekly": 1.0, "Monthly": 1.1}
adj_inventory *= freq_map[order_freq]

# Recompute adjusted balance sheet lines
adj_current_assets = base_proj['Cash'] + base_proj['Accounts Receivable'] + adj_inventory
adj_current_liabilities = base_proj['Current Liabilities']
adj_working_capital = adj_current_assets - adj_current_liabilities
adj_quick_assets = adj_current_assets - adj_inventory
adj_total_assets = base_proj['Total Assets']
adj_net_income = base_proj['Net Income'] * (adj_revenue / base_proj['Revenue'])

# Ratios calculation helper
def compute_ratios(ca, cl, inv, ni, rev, ta):
    cr = ca / cl if cl else np.nan
    qr = (ca - inv) / cl if cl else np.nan
    wcr = (ca - cl) / ta if ta else np.nan
    npm = ni / rev if rev else np.nan
    return cr, qr, wcr, npm

# Base vs. adjusted ratios
base_cr, base_qr, base_wcr, base_npm = compute_ratios(
    base_proj['Current Assets'], base_proj['Current Liabilities'], base_proj['Inventory'],
    base_proj['Net Income'], base_proj['Revenue'], base_proj['Total Assets']
)
adj_cr, adj_qr, adj_wcr, adj_npm = compute_ratios(
    adj_current_assets, adj_current_liabilities, adj_inventory,
    adj_net_income, adj_revenue, adj_total_assets
)

# Display base vs adjusted metrics
st.header(f"2025 Forecast (Base vs. Adjusted)")
result_df = pd.DataFrame({
    'Metric': ['Revenue', 'COGS', 'Inventory Asset', 'Current Assets', 'Current Liabilities',
               'Working Capital', 'Quick Assets', 'Total Assets', 'Net Income'],
    'Base Case': [
        base_proj['Revenue'], base_proj['COGS'], base_proj['Inventory'], base_proj['Current Assets'],
        base_proj['Current Liabilities'], base_proj['Current Assets'] - base_proj['Current Liabilities'],
        base_proj['Current Assets'] - base_proj['Inventory'], base_proj['Total Assets'], base_proj['Net Income']
    ],
    'Adjusted': [
        adj_revenue, adj_cogs, adj_inventory, adj_current_assets, adj_current_liabilities,
        adj_working_capital, adj_quick_assets, adj_total_assets, adj_net_income
    ]
})
st.dataframe(result_df.style.format({1: "{:.2f}", 2: "{:.2f}"}))

# Display ratio comparison
st.subheader("Key Financial Ratios")
ratios_df = pd.DataFrame({
    'Ratio': ['Current Ratio', 'Quick Ratio', 'Working Capital Ratio', 'Net Profit Margin'],
    'Base 2025': [base_cr, base_qr, base_wcr, base_npm],
    'Adjusted 2025': [adj_cr, adj_qr, adj_wcr, adj_npm]
})
st.table(ratios_df.style.format({1: "{:.2f}", 2: "{:.2f}"}))

# Assumptions & explanations
st.markdown("---")
st.subheader("Assumptions & Explanations")
st.markdown("- Base 2025 values are directly calculated from the uploaded Excel file using CAGR up to 2023.")
st.markdown("- Demand outlook: Pessimistic = -10%, Baseline = 0%, Optimistic = +10% on Revenue & COGS.")
st.markdown("- Inventory budget caps the projected inventory asset; ordering frequency modifies inventory by: Weekly (-10%), Bi-weekly (0%), Monthly (+10%).")
st.markdown(
    "**What do changes in ratios mean?**  
- **Current Ratio**: higher => more liquidity to cover short-term debts; lower => potential liquidity strain.  
- **Quick Ratio**: higher => strong ability to meet immediate obligations without selling inventory; lower => risk if inventory isn’t liquid.  
- **Working Capital Ratio**: higher => more working capital relative to assets; lower => less buffer, may affect operations.  
- **Net Profit Margin**: higher => more profitability per euro of revenue; lower => cost pressures or lower efficiency."
)
