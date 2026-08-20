import os
import pandas as pd
import numpy as np

# ============================================================
# TRAFFICX - XGBOOST V2 FEATURE ENGINEERING
# ============================================================

INPUT_FILE = r"D:\TRAFFICX\road_datasets\trafficx_ml_dataset.csv"

OUTPUT_FILE = r"D:\TRAFFICX\road_datasets\trafficx_xgboost_v2_dataset.csv"

print("""
========================================
 TRAFFICX - XGBOOST V2
 TEMPORAL FEATURE ENGINEERING
========================================
""")

print("Loading ML dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Input rows: {len(df):,}")

# ============================================================
# ACTIVE ROAD FILTER
# ============================================================

print("""
========================================
 Active-road filtering
========================================
""")

df = df[
    (df["vehicle_count"] > 0) |
    (df["future_vehicle_count"] > 0)
].copy()

print(f"Rows retained: {len(df):,}")

# ============================================================
# SORT TEMPORALLY
# ============================================================

print("""
========================================
 Sorting temporal data
========================================
""")

df = df.sort_values(
    ["scenario", "road_id", "step"]
).reset_index(drop=True)

# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_cols = [
    "average_speed_kmh",
    "vehicle_count",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m"
]

# Make sure numeric
for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df[numeric_cols] = df[numeric_cols].fillna(0)

# ============================================================
# TEMPORAL DIFFERENCES
# ============================================================

print("""
========================================
 Creating temporal change features
========================================
""")

group = df.groupby(
    ["scenario", "road_id"],
    sort=False
)

# Change from previous simulation step

df["speed_change"] = group[
    "average_speed_kmh"
].diff().fillna(0)

df["vehicle_change"] = group[
    "vehicle_count"
].diff().fillna(0)

df["stopped_change"] = group[
    "stopped_vehicles"
].diff().fillna(0)

df["waiting_change"] = group[
    "average_waiting_time"
].diff().fillna(0)

df["density_change"] = group[
    "density_veh_per_km"
].diff().fillna(0)

df["queue_change"] = group[
    "queue_length_estimate_m"
].diff().fillna(0)

# ============================================================
# MULTI-STEP CHANGE
# ============================================================

print("Creating multi-step temporal features...")

for lag in [5, 15, 30, 60]:

    df[f"speed_change_{lag}s"] = (
        df["average_speed_kmh"]
        - group["average_speed_kmh"].shift(lag)
    ).fillna(0)

    df[f"density_change_{lag}s"] = (
        df["density_veh_per_km"]
        - group["density_veh_per_km"].shift(lag)
    ).fillna(0)

    df[f"queue_change_{lag}s"] = (
        df["queue_length_estimate_m"]
        - group["queue_length_estimate_m"].shift(lag)
    ).fillna(0)

    df[f"waiting_change_{lag}s"] = (
        df["average_waiting_time"]
        - group["average_waiting_time"].shift(lag)
    ).fillna(0)

# ============================================================
# ROLLING FEATURES
# ============================================================

print("Creating rolling traffic features...")

for window in [15, 30, 60]:

    df[f"speed_mean_{window}s"] = (
        group["average_speed_kmh"]
        .transform(
            lambda x: x.rolling(
                window,
                min_periods=1
            ).mean()
        )
    )

    df[f"density_mean_{window}s"] = (
        group["density_veh_per_km"]
        .transform(
            lambda x: x.rolling(
                window,
                min_periods=1
            ).mean()
        )
    )

    df[f"queue_mean_{window}s"] = (
        group["queue_length_estimate_m"]
        .transform(
            lambda x: x.rolling(
                window,
                min_periods=1
            ).mean()
        )
    )

    df[f"waiting_mean_{window}s"] = (
        group["average_waiting_time"]
        .transform(
            lambda x: x.rolling(
                window,
                min_periods=1
            ).mean()
        )
    )

# ============================================================
# ACCELERATION / TREND
# ============================================================

print("Creating trend features...")

df["speed_acceleration"] = (
    df["speed_change"]
    - group["speed_change"].shift(1).fillna(0)
)

df["density_acceleration"] = (
    df["density_change"]
    - group["density_change"].shift(1).fillna(0)
)

df["queue_acceleration"] = (
    df["queue_change"]
    - group["queue_change"].shift(1).fillna(0)
)

# ============================================================
# CURRENT CONGESTION ENCODING
# ============================================================

print("Encoding current congestion...")

congestion_map = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CONGESTED": 3
}

df["current_congestion_encoded"] = (
    df["congestion_level"]
    .map(congestion_map)
    .fillna(0)
)

# ============================================================
# SCENARIO ENCODING
# ============================================================

scenario_map = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "congested": 3
}

df["scenario_encoded"] = (
    df["scenario"]
    .str.lower()
    .map(scenario_map)
    .fillna(0)
)

# ============================================================
# REMOVE UNNECESSARY COLUMNS
# ============================================================

print("Preparing final feature set...")

feature_columns = [

    # Static
    "road_length_m",

    # Current state
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",

    # Current congestion
    "current_congestion_encoded",

    # Scenario
    "scenario_encoded",

    # Instant changes
    "speed_change",
    "vehicle_change",
    "stopped_change",
    "waiting_change",
    "density_change",
    "queue_change",

    # Multi-step changes
    "speed_change_5s",
    "speed_change_15s",
    "speed_change_30s",
    "speed_change_60s",

    "density_change_5s",
    "density_change_15s",
    "density_change_30s",
    "density_change_60s",

    "queue_change_5s",
    "queue_change_15s",
    "queue_change_30s",
    "queue_change_60s",

    "waiting_change_5s",
    "waiting_change_15s",
    "waiting_change_30s",
    "waiting_change_60s",

    # Rolling averages
    "speed_mean_15s",
    "speed_mean_30s",
    "speed_mean_60s",

    "density_mean_15s",
    "density_mean_30s",
    "density_mean_60s",

    "queue_mean_15s",
    "queue_mean_30s",
    "queue_mean_60s",

    "waiting_mean_15s",
    "waiting_mean_30s",
    "waiting_mean_60s",

    # Trend
    "speed_acceleration",
    "density_acceleration",
    "queue_acceleration"
]

target_column = "future_congestion"

# ============================================================
# KEEP REQUIRED COLUMNS
# ============================================================

final_columns = (
    ["scenario", "step", "road_id"]
    + feature_columns
    + [target_column]
)

df = df[final_columns]

# ============================================================
# REMOVE INVALID ROWS
# ============================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.dropna()

# ============================================================
# SAVE
# ============================================================

print("""
========================================
 V2 DATASET SUMMARY
========================================
""")

print(f"Rows       : {len(df):,}")
print(f"Features   : {len(feature_columns)}")
print(f"Columns    : {len(df.columns)}")

print("""
Target distribution:
""")

print(
    df[target_column].value_counts()
)

print("""
Target percentage:
""")

print(
    (df[target_column].value_counts(normalize=True) * 100)
    .round(2)
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("""
========================================
 XGBOOST V2 DATASET CREATED
========================================
""")

print(f"Output: {OUTPUT_FILE}")

print("""
Temporal features added:
  - Short-term changes
  - 5/15/30/60 second changes
  - 15/30/60 second rolling means
  - Acceleration/trend features
  - Current congestion state
  - Scenario encoding
""")