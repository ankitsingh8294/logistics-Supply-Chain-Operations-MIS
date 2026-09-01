"""
generate_data.py

Generates a fictional but logically consistent logistics/supply chain
transaction dataset for a manufacturing company that dispatches goods
from multiple plants to multiple destinations using third-party
transporters and vehicles.

All data is synthetic. No real company, customer, or personal data
is used anywhere in this script or its output.

Run:
    python src/generate_data.py

Output (written to ../data/ relative to this script):
    logistics_transactions.csv
    plants.csv
    vehicles.csv
    transporters.csv
    products.csv
"""

import os
import numpy as np
import pandas as pd

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

N_TRIPS = 12000  # generated, later trimmed to a clean 1000+ row set after filtering
START_DATE = pd.Timestamp("2025-01-01")
END_DATE = pd.Timestamp("2025-12-31")

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. MASTER DATA
# ---------------------------------------------------------------------------

plants = pd.DataFrame([
    {"Plant_ID": "PL01", "Plant_Name": "Pune Manufacturing Unit", "City": "Pune", "State": "Maharashtra"},
    {"Plant_ID": "PL02", "Plant_Name": "Chennai Production Plant", "City": "Chennai", "State": "Tamil Nadu"},
    {"Plant_ID": "PL03", "Plant_Name": "Ludhiana Fabrication Unit", "City": "Ludhiana", "State": "Punjab"},
    {"Plant_ID": "PL04", "Plant_Name": "Vadodara Processing Plant", "City": "Vadodara", "State": "Gujarat"},
    {"Plant_ID": "PL05", "Plant_Name": "Hyderabad Assembly Unit", "City": "Hyderabad", "State": "Telangana"},
    {"Plant_ID": "PL06", "Plant_Name": "Indore Manufacturing Unit", "City": "Indore", "State": "Madhya Pradesh"},
])

destinations = pd.DataFrame([
    {"Destination": "Delhi NCR", "State": "Delhi"},
    {"Destination": "Mumbai", "State": "Maharashtra"},
    {"Destination": "Bengaluru", "State": "Karnataka"},
    {"Destination": "Kolkata", "State": "West Bengal"},
    {"Destination": "Ahmedabad", "State": "Gujarat"},
    {"Destination": "Jaipur", "State": "Rajasthan"},
    {"Destination": "Lucknow", "State": "Uttar Pradesh"},
    {"Destination": "Nagpur", "State": "Maharashtra"},
    {"Destination": "Coimbatore", "State": "Tamil Nadu"},
    {"Destination": "Bhopal", "State": "Madhya Pradesh"},
    {"Destination": "Patna", "State": "Bihar"},
    {"Destination": "Guwahati", "State": "Assam"},
])

transporter_regions = [
    "Maharashtra", "Tamil Nadu", "Punjab", "Gujarat", "Telangana",
    "Madhya Pradesh", "Delhi", "Karnataka", "West Bengal", "Rajasthan",
]
transporter_names = [
    "Bharat Road Carriers", "Shree Balaji Logistics", "Vishal Transport Co.",
    "National Freight Movers", "Speedway Logistics Pvt Ltd", "Ganesh Roadlines",
    "Om Sai Transport", "Kaveri Cargo Movers", "Sunrise Logistics Solutions",
    "Metro Freight Carriers", "Reliable Roadways", "Trident Transport Services",
    "Punjab Truck Union", "Coastal Cargo Carriers", "Apex Logistics India",
    "Shakti Road Carriers", "United Freight Corporation", "Deccan Transport Co.",
]
transporters = pd.DataFrame({
    "Transporter_ID": [f"TR{str(i+1).zfill(2)}" for i in range(len(transporter_names))],
    "Transporter_Name": transporter_names,
    "Region": rng.choice(transporter_regions, size=len(transporter_names)),
})
# reliability score drives on-time performance per transporter (not exported, used for simulation)
transporter_reliability = dict(zip(
    transporters["Transporter_ID"],
    rng.uniform(0.60, 0.95, size=len(transporters))
))
# small cost multiplier variation between transporters (per-km rate variance)
transporter_rate_factor = dict(zip(
    transporters["Transporter_ID"],
    rng.uniform(0.90, 1.15, size=len(transporters))
))

vehicle_types = [
    ("Open Truck 6 Tyre", 9),
    ("Open Truck 10 Tyre", 16),
    ("Container 20ft", 18),
    ("Container 32ft SXL", 22),
    ("Container 32ft MXL", 28),
    ("Trailer 40ft", 35),
]
n_vehicles = 60
veh_type_choices = rng.choice(len(vehicle_types), size=n_vehicles)
vehicles = pd.DataFrame({
    "Vehicle_ID": [f"VH{str(i+1).zfill(3)}" for i in range(n_vehicles)],
    "Vehicle_Type": [vehicle_types[i][0] for i in veh_type_choices],
    "Capacity_Tons": [vehicle_types[i][1] for i in veh_type_choices],
    "Transporter_ID": rng.choice(transporters["Transporter_ID"], size=n_vehicles),
})
vehicles = vehicles.merge(transporters[["Transporter_ID", "Transporter_Name"]], on="Transporter_ID", how="left")

# Per-vehicle utilization tendency: most vehicles load well, some run chronically
# under-loaded (older vehicles, thin/short routes, lighter product mixes).
vehicle_util_bias = {}
for vid in vehicles["Vehicle_ID"]:
    if rng.random() < 0.20:  # ~20% of the fleet is consistently under-utilized
        vehicle_util_bias[vid] = rng.uniform(0.55, 0.75)
    else:
        vehicle_util_bias[vid] = rng.uniform(0.85, 1.0)

products = pd.DataFrame([
    {"Product_ID": "PD01", "Product_Name": "Steel Coils", "Product_Category": "Metals"},
    {"Product_ID": "PD02", "Product_Name": "Steel Pipes", "Product_Category": "Metals"},
    {"Product_ID": "PD03", "Product_Name": "Cement Bags", "Product_Category": "Construction Materials"},
    {"Product_ID": "PD04", "Product_Name": "PVC Granules", "Product_Category": "Chemicals & Polymers"},
    {"Product_ID": "PD05", "Product_Name": "Auto Components", "Product_Category": "Automotive"},
    {"Product_ID": "PD06", "Product_Name": "Electrical Cables", "Product_Category": "Electricals"},
    {"Product_ID": "PD07", "Product_Name": "Packaged Tiles", "Product_Category": "Construction Materials"},
    {"Product_ID": "PD08", "Product_Name": "Textile Rolls", "Product_Category": "Textiles"},
]).sample(frac=1, random_state=1).reset_index(drop=True)

# Approximate distance (km) from each plant to each destination.
# Distances are fictional but kept broadly realistic and internally consistent
# (a plant is ~0 km from the destination that matches its own city/state,
# and distances scale with how "far" states typically are from one another).
plant_city_state = plants.set_index("Plant_ID")[["City", "State"]].to_dict("index")

base_distance_matrix = {}
# Rough relative distance bands between source states and destination hubs,
# derived only for the purpose of generating an internally consistent dataset.
state_hub_distance = {
    ("Maharashtra", "Delhi NCR"): 1420, ("Maharashtra", "Mumbai"): 150,
    ("Maharashtra", "Bengaluru"): 840, ("Maharashtra", "Kolkata"): 1960,
    ("Maharashtra", "Ahmedabad"): 530, ("Maharashtra", "Jaipur"): 1150,
    ("Maharashtra", "Lucknow"): 1420, ("Maharashtra", "Nagpur"): 480,
    ("Maharashtra", "Coimbatore"): 1120, ("Maharashtra", "Bhopal"): 660,
    ("Maharashtra", "Patna"): 1680, ("Maharashtra", "Guwahati"): 2350,

    ("Tamil Nadu", "Delhi NCR"): 2180, ("Tamil Nadu", "Mumbai"): 1330,
    ("Tamil Nadu", "Bengaluru"): 340, ("Tamil Nadu", "Kolkata"): 1670,
    ("Tamil Nadu", "Ahmedabad"): 1870, ("Tamil Nadu", "Jaipur"): 2160,
    ("Tamil Nadu", "Lucknow"): 2160, ("Tamil Nadu", "Nagpur"): 1280,
    ("Tamil Nadu", "Coimbatore"): 500, ("Tamil Nadu", "Bhopal"): 1620,
    ("Tamil Nadu", "Patna"): 2260, ("Tamil Nadu", "Guwahati"): 2830,

    ("Punjab", "Delhi NCR"): 310, ("Punjab", "Mumbai"): 1580,
    ("Punjab", "Bengaluru"): 2170, ("Punjab", "Kolkata"): 1650,
    ("Punjab", "Ahmedabad"): 1080, ("Punjab", "Jaipur"): 480,
    ("Punjab", "Lucknow"): 730, ("Punjab", "Nagpur"): 1230,
    ("Punjab", "Coimbatore"): 2530, ("Punjab", "Bhopal"): 980,
    ("Punjab", "Patna"): 1220, ("Punjab", "Guwahati"): 1980,

    ("Gujarat", "Delhi NCR"): 950, ("Gujarat", "Mumbai"): 530,
    ("Gujarat", "Bengaluru"): 1520, ("Gujarat", "Kolkata"): 1980,
    ("Gujarat", "Ahmedabad"): 120, ("Gujarat", "Jaipur"): 660,
    ("Gujarat", "Lucknow"): 1200, ("Gujarat", "Nagpur"): 850,
    ("Gujarat", "Coimbatore"): 1660, ("Gujarat", "Bhopal"): 590,
    ("Gujarat", "Patna"): 1650, ("Gujarat", "Guwahati"): 2420,

    ("Telangana", "Delhi NCR"): 1580, ("Telangana", "Mumbai"): 710,
    ("Telangana", "Bengaluru"): 570, ("Telangana", "Kolkata"): 1500,
    ("Telangana", "Ahmedabad"): 1160, ("Telangana", "Jaipur"): 1360,
    ("Telangana", "Lucknow"): 1420, ("Telangana", "Nagpur"): 500,
    ("Telangana", "Coimbatore"): 730, ("Telangana", "Bhopal"): 780,
    ("Telangana", "Patna"): 1560, ("Telangana", "Guwahati"): 2130,

    ("Madhya Pradesh", "Delhi NCR"): 780, ("Madhya Pradesh", "Mumbai"): 660,
    ("Madhya Pradesh", "Bengaluru"): 1300, ("Madhya Pradesh", "Kolkata"): 1250,
    ("Madhya Pradesh", "Ahmedabad"): 590, ("Madhya Pradesh", "Jaipur"): 480,
    ("Madhya Pradesh", "Lucknow"): 620, ("Madhya Pradesh", "Nagpur"): 290,
    ("Madhya Pradesh", "Coimbatore"): 1560, ("Madhya Pradesh", "Bhopal"): 15,
    ("Madhya Pradesh", "Patna"): 1080, ("Madhya Pradesh", "Guwahati"): 1850,
}

# Route naming helper
def route_name(plant_row, dest):
    return f"{plant_row['City']} - {dest}"

# ---------------------------------------------------------------------------
# 2. TRANSACTION-LEVEL SIMULATION
# ---------------------------------------------------------------------------

delay_reasons_pool = [
    "Traffic Congestion", "Vehicle Breakdown", "Weather Conditions",
    "Documentation Delay", "Loading Delay at Plant", "Driver Unavailability",
    "Route Diversion", "Customer Site Congestion", "Toll/Checkpoint Delay",
    "Not Applicable",
]

rows = []
plant_ids = plants["Plant_ID"].tolist()
dest_list = destinations["Destination"].tolist()
product_ids = products["Product_ID"].tolist()
vehicle_ids = vehicles["Vehicle_ID"].tolist()

# Plant dispatch-volume weighting so some plants are naturally larger
plant_weights = rng.dirichlet(np.array([3, 2.4, 1.6, 2.0, 2.6, 1.4]))
dest_weights = rng.dirichlet(np.ones(len(dest_list)) * 1.3)

date_range_days = (END_DATE - START_DATE).days

trip_counter = 1
for i in range(N_TRIPS):
    plant_id = rng.choice(plant_ids, p=plant_weights)
    plant_row = plant_city_state[plant_id]
    plant_state = plant_row["State"]

    destination = rng.choice(dest_list, p=dest_weights)
    key = (plant_state, destination)
    base_km = base_distance_matrix.get(key)
    if base_km is None:
        base_km = state_hub_distance.get(key, rng.integers(300, 2200))
    distance_km = max(20, int(rng.normal(base_km, base_km * 0.05)))

    vehicle_id = rng.choice(vehicle_ids)
    veh_row = vehicles.loc[vehicles["Vehicle_ID"] == vehicle_id].iloc[0]
    transporter_id = veh_row["Transporter_ID"]
    transporter_name = veh_row["Transporter_Name"]
    vehicle_type = veh_row["Vehicle_Type"]
    capacity = veh_row["Capacity_Tons"]

    # Loaded quantity: driven by the vehicle's utilization tendency, with trip-to-trip noise
    util_center = vehicle_util_bias[vehicle_id]
    quantity_tons = round(capacity * np.clip(rng.normal(util_center, 0.06), 0.35, 1.0), 2)

    product_id = rng.choice(product_ids)

    dispatch_offset = int(rng.integers(0, date_range_days + 1))
    dispatch_date = START_DATE + pd.Timedelta(days=dispatch_offset)

    loading_start = dispatch_date + pd.Timedelta(hours=int(rng.integers(6, 11)),
                                                  minutes=int(rng.integers(0, 60)))
    loading_duration_hr = max(0.5, rng.normal(2.2, 0.7))
    loading_end = loading_start + pd.Timedelta(hours=loading_duration_hr)

    weighbridge_time = loading_end + pd.Timedelta(minutes=int(rng.integers(15, 60)))
    gate_out_time = weighbridge_time + pd.Timedelta(minutes=int(rng.integers(10, 45)))

    # Average running speed depends loosely on vehicle type (heavier => slightly slower)
    base_speed = {
        "Open Truck 6 Tyre": 46, "Open Truck 10 Tyre": 42,
        "Container 20ft": 44, "Container 32ft SXL": 40,
        "Container 32ft MXL": 38, "Trailer 40ft": 36,
    }[vehicle_type]
    avg_speed = max(28, rng.normal(base_speed, 4))
    transit_hours = distance_km / avg_speed

    # Reliability-driven extra delay (hours), transporter-specific
    reliability = transporter_reliability[transporter_id]
    # lower reliability -> higher chance & size of delay
    delay_probability = 1 - reliability
    has_delay_event = rng.random() < delay_probability
    extra_delay_hours = 0.0
    delay_reason = "Not Applicable"
    if has_delay_event:
        extra_delay_hours = rng.gamma(shape=2.0, scale=10.0)  # hours
        delay_reason = rng.choice(delay_reasons_pool[:-1])

    total_transit_hours = transit_hours + extra_delay_hours
    actual_delivery_datetime = gate_out_time + pd.Timedelta(hours=total_transit_hours)

    # Expected delivery date: based on typical transit time for the distance (no delay buffer),
    # plus a standard 1-day handling allowance, rounded to a date.
    expected_transit_hours = transit_hours + rng.uniform(4, 10)  # standard buffer
    expected_delivery_datetime = gate_out_time + pd.Timedelta(hours=expected_transit_hours)

    expected_delivery_date = expected_delivery_datetime.normalize()
    actual_delivery_date = actual_delivery_datetime.normalize()

    delay_days = max(0, (actual_delivery_date - expected_delivery_date).days)
    on_time_flag = 1 if actual_delivery_date <= expected_delivery_date else 0
    delivery_status = "On Time" if on_time_flag == 1 else "Delayed"
    if delay_days == 0 and on_time_flag == 0:
        delay_days = 1  # same-day-but-after-cutoff edge case still counts as minor delay

    if on_time_flag == 1:
        delay_reason = "Not Applicable"
    elif delay_reason == "Not Applicable":
        # ensure a delayed trip always has an assigned cause
        delay_reason = rng.choice(delay_reasons_pool[:-1])

    # Freight cost: driven by distance, quantity, and transporter rate factor,
    # plus a small fixed loading/handling charge.
    rate_per_ton_km = 2.35 * transporter_rate_factor[transporter_id]
    freight_cost = round(distance_km * quantity_tons * rate_per_ton_km * rng.uniform(0.94, 1.06)
                          + rng.uniform(400, 900), 2)

    route = route_name(plant_row, destination)

    rows.append({
        "Trip_ID": f"TRIP{str(trip_counter).zfill(6)}",
        "Dispatch_Date": dispatch_date.date(),
        "Plant_ID": plant_id,
        "Plant_Name": plants.set_index("Plant_ID").loc[plant_id, "Plant_Name"],
        "Destination": destination,
        "Route": route,
        "Product_ID": product_id,
        "Product_Name": products.set_index("Product_ID").loc[product_id, "Product_Name"],
        "Quantity_Tons": quantity_tons,
        "Vehicle_ID": vehicle_id,
        "Vehicle_Type": vehicle_type,
        "Vehicle_Capacity_Tons": capacity,
        "Transporter_ID": transporter_id,
        "Transporter_Name": transporter_name,
        "Loading_Start_Time": loading_start,
        "Loading_End_Time": loading_end,
        "Weighbridge_Time": weighbridge_time,
        "Gate_Out_Time": gate_out_time,
        "Expected_Delivery_Date": expected_delivery_date.date(),
        "Actual_Delivery_Date": actual_delivery_date.date(),
        "Delivery_Status": delivery_status,
        "Delay_Days": int(delay_days),
        "Delay_Reason": delay_reason,
        "Freight_Cost": freight_cost,
        "Distance_KM": distance_km,
        "On_Time_Flag": on_time_flag,
    })

    trip_counter += 1

df = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# 3. DATA QUALITY / CLEANUP
# ---------------------------------------------------------------------------

# Drop any accidental duplicate Trip IDs (should not occur, kept as a safeguard)
df = df.drop_duplicates(subset="Trip_ID").reset_index(drop=True)

# Drop rows with missing critical fields (safeguard)
critical_cols = [
    "Trip_ID", "Dispatch_Date", "Plant_ID", "Destination", "Route",
    "Quantity_Tons", "Vehicle_ID", "Transporter_ID", "Expected_Delivery_Date",
    "Actual_Delivery_Date", "Freight_Cost", "Distance_KM",
]
df = df.dropna(subset=critical_cols).reset_index(drop=True)

# Validate: expected/actual dates parse correctly and Actual is never before Gate Out date
df["Dispatch_Date"] = pd.to_datetime(df["Dispatch_Date"])
df["Expected_Delivery_Date"] = pd.to_datetime(df["Expected_Delivery_Date"])
df["Actual_Delivery_Date"] = pd.to_datetime(df["Actual_Delivery_Date"])
df = df[df["Actual_Delivery_Date"] >= df["Dispatch_Date"]].reset_index(drop=True)

# Validate numeric fields are positive
df = df[(df["Quantity_Tons"] > 0) & (df["Freight_Cost"] > 0) & (df["Distance_KM"] > 0)].reset_index(drop=True)

# Recompute On_Time_Flag and Delivery_Status directly from the two dates
# (single source of truth, avoids any inconsistency from the simulation step)
df["On_Time_Flag"] = (df["Actual_Delivery_Date"] <= df["Expected_Delivery_Date"]).astype(int)
df["Delivery_Status"] = np.where(df["On_Time_Flag"] == 1, "On Time", "Delayed")
df["Delay_Days"] = (df["Actual_Delivery_Date"] - df["Expected_Delivery_Date"]).dt.days.clip(lower=0)
df.loc[df["On_Time_Flag"] == 1, "Delay_Reason"] = "Not Applicable"
df.loc[(df["On_Time_Flag"] == 0) & (df["Delay_Reason"] == "Not Applicable"), "Delay_Reason"] = "Documentation Delay"

# Trim to a clean, review-ready sample of ~1,050 trips while keeping full-year,
# multi-plant, multi-transporter coverage (portfolio-sized dataset, not a raw dump)
df = df.sample(n=min(1050, len(df)), random_state=RANDOM_SEED).sort_values("Dispatch_Date").reset_index(drop=True)

# Format date columns back to plain dates for CSV output
for col in ["Dispatch_Date", "Expected_Delivery_Date", "Actual_Delivery_Date"]:
    df[col] = df[col].dt.strftime("%Y-%m-%d")
for col in ["Loading_Start_Time", "Loading_End_Time", "Weighbridge_Time", "Gate_Out_Time"]:
    df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d %H:%M")

column_order = [
    "Trip_ID", "Dispatch_Date", "Plant_ID", "Plant_Name", "Destination", "Route",
    "Product_ID", "Product_Name", "Quantity_Tons", "Vehicle_ID", "Vehicle_Type",
    "Vehicle_Capacity_Tons", "Transporter_ID", "Transporter_Name",
    "Loading_Start_Time", "Loading_End_Time", "Weighbridge_Time", "Gate_Out_Time",
    "Expected_Delivery_Date", "Actual_Delivery_Date", "Delivery_Status",
    "Delay_Days", "Delay_Reason", "Freight_Cost", "Distance_KM", "On_Time_Flag",
]
df = df[column_order]

# ---------------------------------------------------------------------------
# 4. EXPORT
# ---------------------------------------------------------------------------

df.to_csv(os.path.join(OUT_DIR, "logistics_transactions.csv"), index=False)
plants.to_csv(os.path.join(OUT_DIR, "plants.csv"), index=False)
vehicles[["Vehicle_ID", "Vehicle_Type", "Capacity_Tons", "Transporter_ID", "Transporter_Name"]].to_csv(
    os.path.join(OUT_DIR, "vehicles.csv"), index=False)
transporters.to_csv(os.path.join(OUT_DIR, "transporters.csv"), index=False)
products.to_csv(os.path.join(OUT_DIR, "products.csv"), index=False)

print(f"Generated {len(df)} logistics transactions.")
print(f"Plants: {df['Plant_ID'].nunique()} | Destinations: {df['Destination'].nunique()} | "
      f"Transporters: {df['Transporter_ID'].nunique()} | Vehicles: {df['Vehicle_ID'].nunique()}")
print(f"Date range: {df['Dispatch_Date'].min()} to {df['Dispatch_Date'].max()}")
print("Files written to:", OUT_DIR)
