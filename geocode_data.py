import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# ─── Helpers ───────────────────────────────────────────────────────────────────
def clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names: strip, lowercase, remove spaces/punctuation."""
    df = df.copy()
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r"[ \-()]+", "", regex=True)
          .str.replace(r"[^\w]",    "", regex=True)
    )
    return df

# ─── Load & Clean CSVs ─────────────────────────────────────────────────────────
print("Loading and cleaning CSVs...")
locs = clean_cols(pd.read_csv("data/Bushnell_Locations.csv"))
sups = clean_cols(pd.read_csv("data/Bushnell_Supplier_List_With_Tariffs_And_Logistics.csv"))

print("Locations columns:", locs.columns.tolist())
print("Suppliers columns:", sups.columns.tolist())

# ─── Rename Key Columns ────────────────────────────────────────────────────────
# Adjust if your raw headers differ
locs = locs.rename(columns={
    "sitelocation": "marketcode",
    "name":         "marketname"
})
sups = sups.rename(columns={
    "countryoforigin": "countryorigin"
})

print("After rename - Locations columns:", locs.columns.tolist())
print("After rename - Suppliers columns:", sups.columns.tolist())

# ─── Geocode Preparation ─────────────────────────────────────────────────────────
geolocator = Nominatim(user_agent="tariff_app_pre")
geocode     = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# 1) Geocode unique markets
mk = locs[["marketcode","marketname"]].drop_duplicates().copy()
mk["coords"]    = mk["marketname"].apply(geocode)
mk["marketlat"] = mk["coords"].apply(lambda c: c.latitude if c else None)
mk["marketlon"] = mk["coords"].apply(lambda c: c.longitude if c else None)
mk = mk.drop(columns=["coords"])
print(f"Geocoded {len(mk)} markets.")

# 2) Geocode unique origins
og = pd.DataFrame(sups["countryorigin"].unique(), columns=["countryorigin"])
og["coords"]    = og["countryorigin"].apply(geocode)
og["originlat"] = og["coords"].apply(lambda c: c.latitude if c else None)
og["originlon"] = og["coords"].apply(lambda c: c.longitude if c else None)
og = og.drop(columns=["coords"])
print(f"Geocoded {len(og)} origins.")

# ─── Merge Back & Write ─────────────────────────────────────────────────────────
locs = locs.merge(mk, on=["marketcode","marketname"], how="left")
sups = sups.merge(og, on="countryorigin", how="left")

locs.to_csv("data/Bushnell_Locations_geocoded.csv", index=False)
sups.to_csv("data/Bushnell_Supplier_List_With_Tariffs_And_Logistics_geocoded.csv", index=False)

print("✅ Geocoding complete. Enriched files written: ")
print("  data/Bushnell_Locations_geocoded.csv")
print("  data/Bushnell_Supplier_List_With_Tariffs_And_Logistics_geocoded.csv")
