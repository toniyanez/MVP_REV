import pandas as pd

# Load existing files
locations = pd.read_csv("data/bushnell_locations.csv")
routes = pd.read_csv("data/bushnell_supply_routes.csv")

# Merge country names into routes
routes = routes.merge(locations[['location_id', 'country']], left_on='origin_location_id', right_on='location_id')
routes = routes.rename(columns={'country': 'origin_country'}).drop(columns='location_id')
routes = routes.merge(locations[['location_id', 'country']], left_on='destination_location_id', right_on='location_id')
routes = routes.rename(columns={'country': 'destination_country'}).drop(columns='location_id')

# Define tariff matrix (EXAMPLE values — customize this!)
tariff_matrix = pd.DataFrame([
    {"origin_country": "China", "destination_country": "USA", "product_category": "Riflescopes", "tariff_pct": 25},
    {"origin_country": "China", "destination_country": "USA", "product_category": "Binoculars", "tariff_pct": 20},
    {"origin_country": "Japan", "destination_country": "USA", "product_category": "Riflescopes", "tariff_pct": 5},
    {"origin_country": "Mexico", "destination_country": "USA", "product_category": "Rangefinders", "tariff_pct": 0},
    {"origin_country": "Malaysia", "destination_country": "USA", "product_category": "Launch_Monitors", "tariff_pct": 10},
    {"origin_country": "China", "destination_country": "USA", "product_category": "Red_Dots", "tariff_pct": 30},
    {"origin_country": "China", "destination_country": "USA", "product_category": "Trail_Cameras", "tariff_pct": 15},
    # Add more combinations here
])

# Merge to assign tariff to each route
routes = routes.merge(
    tariff_matrix,
    on=["origin_country", "destination_country", "product_category"],
    how="left"
)

# Fill missing tariffs if needed
routes["tariff_pct"] = routes["tariff_pct"].fillna(0)

# Save result
routes.to_csv("data/bushnell_supply_routes_with_tariffs.csv", index=False)
