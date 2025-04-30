import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# === Streamlit Page Setup ===
st.set_page_config(layout="wide")
st.title("🌏 Bushnell Global Supply Chain Dashboard")
st.markdown("Simulate tariff impacts on profit margins and routes per brand.")

# === Load Data ===
locations = pd.read_csv("data/bushnell_locations.csv")
routes = pd.read_csv("data/bushnell_supply_routes.csv")

# === Merge Countries ===
routes = routes.merge(
    locations[['location_id', 'country']],
    left_on='origin_location_id', right_on='location_id', how='left'
).rename(columns={'country': 'origin_country'}).drop(columns='location_id')

routes = routes.merge(
    locations[['location_id', 'country']],
    left_on='destination_location_id', right_on='location_id', how='left'
).rename(columns={'country': 'destination_country'}).drop(columns='location_id')

# === Tariff Scenario Definitions ===
tariff_scenarios = {
    "Base": {
        ("China", "USA", "Riflescopes"): 25,
        ("China", "USA", "Red_Dots"): 15,
        ("Japan", "USA", "Riflescopes"): 5
    },
    "Extreme Tariff (Scenario 5)": {
        ("China", "USA", "Riflescopes"): 125,
        ("China", "USA", "Red_Dots"): 100,
        ("Japan", "USA", "Riflescopes"): 5
    },
    "Decoupling (Scenario 1)": {
        ("China", "USA", "Riflescopes"): 100,
        ("China", "USA", "Red_Dots"): 90,
        ("Japan", "USA", "Riflescopes"): 5
    }
}

# === Sidebar Scenario Selector ===
st.sidebar.title("Scenario Selection")
selected_scenario = st.sidebar.selectbox("📄 Choose Tariff Scenario", list(tariff_scenarios.keys()))

# === Apply Tariffs ===
def get_tariff(row):
    key = (
        str(row['origin_country']).strip(),
        str(row['destination_country']).strip(),
        str(row['product_category']).strip()
    )
    return tariff_scenarios[selected_scenario].get(key, 0)

routes["tariff_pct"] = routes.apply(get_tariff, axis=1)

# === Simulate Profit Margin Impact ===
routes["base_margin_pct"] = 40  # static base margin assumption
routes["profit_margin_pct"] = (routes["base_margin_pct"] - routes["tariff_pct"]).clip(lower=0)

# === Brand-Level Summary ===
brand_profit = routes.groupby("brand").agg(
    avg_tariff_pct=("tariff_pct", "mean"),
    avg_margin_pct=("profit_margin_pct", "mean"),
    route_count=("product_category", "count")
).reset_index()

# === Merge Coordinates (Clean!) ===
origin_coords = locations[['location_id', 'lat', 'lon', 'site_name']].rename(columns={
    'location_id': 'origin_location_id',
    'lat': 'origin_lat',
    'lon': 'origin_lon',
    'site_name': 'origin_name'
})

dest_coords = locations[['location_id', 'lat', 'lon', 'site_name']].rename(columns={
    'location_id': 'destination_location_id',
    'lat': 'dest_lat',
    'lon': 'dest_lon',
    'site_name': 'dest_name'
})

# Merge origin coordinates
routes = routes.merge(origin_coords, on='origin_location_id', how='left', suffixes=('', '_origin'))
# Merge destination coordinates
routes = routes.merge(dest_coords, on='destination_location_id', how='left', suffixes=('', '_destination'))

# Drop duplicate columns if they exist
routes = routes.loc[:, ~routes.columns.duplicated()]

# === Dashboard Summary ===
st.subheader("📊 Scenario Impact Dashboard")
col1, col2 = st.columns(2)
col1.metric("🚢 Total Routes", len(routes))
col2.metric("📉 Avg Profit Margin", f"{routes['profit_margin_pct'].mean():.1f}%")

st.subheader("💼 Brand-Level Profit Impact")
st.dataframe(brand_profit)

# === MAP Visualization ===
st.subheader("🗺️ Supply Routes with Tariff Effects")
fig = go.Figure()

for _, row in routes.iterrows():
    color = "crimson" if row['tariff_pct'] >= 50 else "gray"
    fig.add_trace(go.Scattergeo(
        lon=[row['origin_lon'], row['dest_lon']],
        lat=[row['origin_lat'], row['dest_lat']],
        mode='lines',
        line=dict(width=2, color=color),
        hoverinfo="text",
        text=(
            f"<b>{row['brand']} - {row['product_category']}</b><br>"
            f"From: {row['origin_name']}<br>To: {row['dest_name']}<br>"
            f"<b>Tariff:</b> {row['tariff_pct']}%<br><b>Margin:</b> {row['profit_margin_pct']}%"
        ),
        opacity=0.7
    ))

fig.add_trace(go.Scattergeo(
    lon=locations["lon"],
    lat=locations["lat"],
    mode='markers',
    text=locations["site_name"],
    marker=dict(size=6, color="black"),
    hoverinfo="text"
))

fig.update_layout(
    geo=dict(
        projection_type="natural earth",
        showland=True,
        landcolor="white",
        oceancolor="lightblue",
        showocean=True,
        lakecolor="lightblue",
        resolution=50,
        lonaxis=dict(range=[90, -80]),
        lataxis=dict(range=[-20, 60])
    ),
    height=1000,
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

# === Optional: Route Table ===
with st.expander("📄 Show Detailed Route Table"):
    st.dataframe(routes[[
        "brand", "product_category", "origin_country", "destination_country",
        "origin_name", "dest_name", "tariff_pct", "profit_margin_pct"
    ]])
