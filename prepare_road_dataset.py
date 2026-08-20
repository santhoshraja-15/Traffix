import pandas as pd
import numpy as np

# ============================================================
# TRAFFICX - Road-Level Feature Engineering
# ============================================================

input_file = r"D:\TRAFFICX\road_level_traffic.csv"
output_file = r"D:\TRAFFICX\road_level_features.csv"

print("\n========================================")
print(" TRAFFICX - FEATURE ENGINEERING")
print("========================================")

# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

df = pd.read_csv(input_file)

print(f"Input rows: {len(df):,}")
print(f"Unique roads: {df['road_id'].nunique():,}")

# ------------------------------------------------------------
# Density
# ------------------------------------------------------------
# Approximation:
# vehicles per kilometer of road
#
# density = vehicles / road_length_km
# ------------------------------------------------------------

df["road_length_km"] = df["road_length_m"] / 1000

df["density_veh_per_km"] = np.where(
    df["road_length_km"] > 0,
    df["vehicle_count"] / df["road_length_km"],
    0
)

# ------------------------------------------------------------
# Occupancy approximation
# ------------------------------------------------------------
#
# We don't yet have exact lane occupancy from SUMO.
# So we create a normalized traffic-load indicator.
#
# This is NOT physical occupancy yet.
# We will replace it with a better SUMO-derived value later.
# ------------------------------------------------------------

df["occupancy_estimate"] = np.minimum(
    df["density_veh_per_km"] / 100,
    1.0
)

# ------------------------------------------------------------
# Queue length approximation
# ------------------------------------------------------------
#
# Stopped vehicles × average vehicle length
# Approximate vehicle length = 5 m
# ------------------------------------------------------------

AVERAGE_VEHICLE_LENGTH = 5.0

df["queue_length_m"] = (
    df["stopped_vehicles"]
    * AVERAGE_VEHICLE_LENGTH
)

# ------------------------------------------------------------
# Congestion level
# ------------------------------------------------------------
#
# Initial rule-based classification.
# We will later tune these thresholds using the generated data.
# ------------------------------------------------------------

def classify_congestion(row):

    speed = row["average_speed_kmh"]
    waiting = row["average_waiting_time"]
    density = row["density_veh_per_km"]

    if (
        speed < 20
        or waiting > 20
        or density > 80
    ):
        return "CONGESTED"

    elif (
        speed < 35
        or waiting > 10
        or density > 50
    ):
        return "HIGH"

    elif (
        speed < 45
        or waiting > 5
        or density > 25
    ):
        return "MEDIUM"

    else:
        return "LOW"


df["congestion_level"] = df.apply(
    classify_congestion,
    axis=1
)

# ------------------------------------------------------------
# Time information
# ------------------------------------------------------------

# SUMO step is currently our time representation.
# We assume one simulation step ≈ one second.

df["simulation_time_sec"] = df["step"]

df["minute"] = (
    df["simulation_time_sec"] // 60
)

# ------------------------------------------------------------
# Sort data
# ------------------------------------------------------------

df = df.sort_values(
    ["road_id", "step"]
).reset_index(drop=True)

# ------------------------------------------------------------
# Select final columns
# ------------------------------------------------------------

output_columns = [
    "step",
    "minute",
    "road_id",
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "road_length_m",
    "density_veh_per_km",
    "occupancy_estimate",
    "queue_length_m",
    "congestion_level"
]

df = df[output_columns]

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

df.to_csv(
    output_file,
    index=False
)

# ------------------------------------------------------------
# Statistics
# ------------------------------------------------------------

print("\nCongestion distribution:")
print(
    df["congestion_level"]
    .value_counts()
)

print("\n========================================")
print(" Feature engineering complete")
print(f" Output: {output_file}")
print("========================================")