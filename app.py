import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import plotly.graph_objects as go

# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()
LOCATIONS_CSV    = os.getenv("LOCATIONS_CSV", "./data/Bushnell_Locations_geocoded.csv")
SUPPLIERS_CSV    = os.getenv("SUPPLIERS_CSV", "./data/Bushnell_Supplier_List_With_Tariffs_And_Logistics_geocoded.csv")
PRODUCTS_CSV     = os.getenv("PRODUCTS_CSV",    "./data/Bushnell_Products_List.csv")
TARIFFS_CSV      = os.getenv("TARIFFS_CSV",     "./data/Bushnell_Market_Products_Tariffs.csv")

# ─── Load & merge ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    locs   = pd.read_csv(LOCATIONS_CSV)
    sups   = pd.read_csv(SUPPLIERS_CSV)
    prods  = pd.read_csv(PRODUCTS_CSV)
    tarifs = pd.read_csv(TARIFFS_CSV)

    # normalize names if needed
    locs   = locs.rename(columns={"sitelocation":"marketcode","name":"marketname"})
    sups   = sups.rename(columns={"countryoforigin":"countryorigin"})
    # merge chain
    df = (
        sups
        .merge(prods,  on="productcode", how="left")
        .merge(tarifs, on=["marketcode","productcode"], how="left")
        .merge(locs,   on="marketcode", how="left")
    )
    # drop any rows without coords or tariff
    df = df.dropna(subset=["originlat","originlon","marketlat","marketlon","tariffrate"])
    return df

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.title("Tariff Impact Globe 🚢🌐")

    # load
    try:
        df = load_data()
        st.sidebar.success(f"Loaded {len(df)} records")
    except Exception as e:
        st.error(f"Error: {e}")
        return

    # filters
    prod_sel   = st.sidebar.multiselect("Product", sorted(df["productname"].unique()))
    market_sel = st.sidebar.multiselect("Market",  sorted(df["marketname"].unique()))
    origin_sel = st.sidebar.multiselect("Origin",  sorted(df["countryorigin"].unique()))

    df_f = df.copy()
    if prod_sel:   df_f = df_f[df_f["productname"].isin(prod_sel)]
    if market_sel: df_f = df_f[df_f["marketname"].isin(market_sel)]
    if origin_sel: df_f = df_f[df_f["countryorigin"].isin(origin_sel)]

    if df_f.empty:
        st.warning("No data for those filters.")
        return

    # build globe
    fig = go.Figure()
    # origins
    fig.add_trace(go.Scattergeo(
        lon=df_f["originlon"], lat=df_f["originlat"],
        mode="markers", marker=dict(size=5,color="red"),
        name="Origins", hovertext=df_f["countryorigin"]
    ))
    # markets
    fig.add_trace(go.Scattergeo(
        lon=df_f["marketlon"], lat=df_f["marketlat"],
        mode="markers", marker=dict(size=5,color="blue"),
        name="Markets", hovertext=df_f["marketname"]
    ))
    # arcs
    for _, r in df_f.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r["originlon"], r["marketlon"]],
            lat=[r["originlat"], r["marketlat"]],
            mode="lines",
            line=dict(width=1,color="green"),
            opacity=0.6, showlegend=False
        ))
    fig.update_layout(
        geo=dict(projection_type="orthographic",showland=True,
                 landcolor="lightgray",showcountries=True,
                 oceancolor="aliceblue",lakecolor="lightblue"),
        margin=dict(l=0,r=0,t=30,b=0)
    )
    st.plotly_chart(fig,use_container_width=True)

if __name__=="__main__":
    main()
