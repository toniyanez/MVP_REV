import streamlit as st
import pandas as pd
import plotly.express as px
import json

# === Load Scenarios from JSON ===
with open("documents/scenarios.json", "r") as f:
    scenarios = json.load(f)

# === Streamlit Setup ===
st.set_page_config(layout="wide")
st.title("📊 Supply Chain Dashboard with Scenarios")

# === Load Data ===
routes = pd.read_csv("data/bushnell_supply_routes.csv")
locations = pd.read_csv("data/bushnell_locations.csv")

# Merge country info
routes = routes.merge(
    locations[['location_id', 'country']],
    left_on='origin_location_id', right_on='location_id', how='left'
).rename(columns={'country': 'origin_country'}).drop(columns=['location_id'])

routes = routes.merge(
    locations[['location_id', 'country']],
    left_on='destination_location_id', right_on='location_id', how='left'
).rename(columns={'country': 'destination_country'}).drop(columns=['location_id'])

# Ensure no duplicate column names
routes = routes.loc[:, ~routes.columns.duplicated()]

# === Sidebar: Scenario Selection ===
st.sidebar.title("Scenario Selection")
scenario_options = list(scenarios.keys()) + ["Custom"]
selected_scenario = st.sidebar.selectbox("Select a Scenario", scenario_options)

# === Custom Scenario Input Fields ===
if selected_scenario == "Custom":
    st.sidebar.subheader("Define Your Custom Scenario")
    tariff_multiplier = st.sidebar.number_input("Tariff Multiplier", min_value=0.0, value=1.0, step=0.1)
    freight_multiplier = st.sidebar.number_input("Freight Multiplier", min_value=0.0, value=1.0, step=0.1)
    sourcing_restrictions = st.sidebar.text_area("Sourcing Restrictions (comma-separated)", value="")
    lead_time_delay_days = st.sidebar.number_input("Lead Time Delay (days)", min_value=0, value=0, step=1)
    revenue_loss_multiplier = st.sidebar.number_input("Revenue Loss Multiplier", min_value=0.0, value=1.0, step=0.1)

    # Convert sourcing restrictions to a list
    sourcing_restrictions = [x.strip() for x in sourcing_restrictions.split(",") if x.strip()]

    # Create the custom scenario
    scenario = {
        "name": "Custom Scenario",
        "tariff_multiplier": tariff_multiplier,
        "freight_multiplier": freight_multiplier,
        "sourcing_restrictions": sourcing_restrictions,
        "lead_time_delay_days": lead_time_delay_days,
        "revenue_loss_multiplier": revenue_loss_multiplier
    }
else:
    # Load the selected predefined scenario
    scenario = scenarios[selected_scenario]

# === Apply Scenario to Data ===
def apply_scenario(data, scenario):
    modified_data = data.copy()

    # Apply tariff multiplier
    modified_data['Tarif_trade_applied'] *= scenario['tariff_multiplier']

    # Apply freight multiplier (if applicable)
    if 'Transport_cost_share' in modified_data.columns:
        modified_data['Transport_cost_share'] *= scenario['freight_multiplier']

    # Apply sourcing restrictions
    if scenario['sourcing_restrictions']:
        restricted_routes = modified_data['origin_country'].isin(scenario['sourcing_restrictions'])
        modified_data.loc[restricted_routes, 'profit_margin'] = 0  # Assume no profit for restricted routes

    # Apply lead time delay (if applicable)
    if 'lead_time_days' in modified_data.columns:
        modified_data['lead_time_days'] += scenario['lead_time_delay_days']

    # Apply revenue loss multiplier
    if 'profit_margin' in modified_data.columns:
        modified_data['profit_margin'] *= (1 - scenario['revenue_loss_multiplier'])

    return modified_data

# Apply the selected or custom scenario
routes = apply_scenario(routes, scenario)

# === Dashboard Visualizations ===
# Brand-level summary
brand_stats = routes.groupby("brand").agg(
    avg_tariff=("Tarif_trade_applied", "mean"),
    avg_transport_cost=("Transport_cost_share", "mean"),
    avg_margin=("profit_margin", "mean"),
    route_count=("product_category", "count")
).reset_index()

st.subheader(f"📈 Impact of {scenario['name']} on Brand-Level Metrics")
fig = px.bar(
    brand_stats, x="brand", y="avg_margin",
    color="avg_tariff",
    color_continuous_scale="reds",
    title=f"Brand-Level Margin Under {scenario['name']}",
    labels={"avg_margin": "Avg. Profit Margin (%)", "avg_tariff": "Avg. Tariff (%)"},
    height=500
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📋 Brand-Level Summary Table")
st.dataframe(brand_stats)

# === Display Scenario Details ===
st.sidebar.subheader("Scenario Details")
st.sidebar.json(scenario)
