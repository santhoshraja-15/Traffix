import os
import pandas as pd
import numpy as np

# ============================================================
# TRAFFICX - XGBOOST V3 FEATURE ENGINEERING
# CLEAN TEMPORAL FORECASTING DATASET
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_ml_dataset.csv"
)

OUTPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_v3_dataset.csv"
)

MIN_ROAD_LENGTH_M = 5.0


print("""
========================================
 TRAFFICX - XGBOOST V3
 CLEAN TEMPORAL FEATURE ENGINEERING
========================================

Prediction horizon:
5 minutes = 300 simulation steps

Temporal features:
5 / 15 / 30 / 60 seconds

Road quality filter:
road_length >= 5 meters
========================================
""")


# ============================================================
# LOAD DATA
# ============================================================

print("Loading ML dataset...")

df = pd.read_csv(INPUT_FILE)

print(
    f"Input rows: {len(df):,}"
)


# ============================================================
# SORT BEFORE ANY FILTERING
# ============================================================

print("""
========================================
 Sorting complete time series
========================================
""")

df = df.sort_values(
    [
        "scenario",
        "road_id",
        "step"
    ]
).reset_index(drop=True)


# ============================================================
# VERIFY TEMPORAL CONTINUITY
# ============================================================

print("""
========================================
 Checking temporal continuity
========================================
""")

step_diff = (
    df.groupby(
        ["scenario", "road_id"]
    )["step"]
    .diff()
)

non_one = (
    step_diff.dropna() != 1
).sum()

print(
    f"Non-consecutive transitions: {non_one:,}"
)

if non_one != 0:
    raise RuntimeError(
        "Temporal continuity check failed."
    )

print(
    "Temporal continuity: OK"
)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_cols = [
    "road_length_m",
    "average_speed_kmh",
    "vehicle_count",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m"
]

for col in numeric_cols:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df[numeric_cols] = (
    df[numeric_cols]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
)


# ============================================================
# GROUP
# ============================================================

group = df.groupby(
    [
        "scenario",
        "road_id"
    ],
    sort=False
)


# ============================================================
# TEMPORAL DIFFERENCES
# ============================================================

print("""
========================================
 Creating temporal changes
========================================
""")

df["speed_change"] = (
    group["average_speed_kmh"]
    .diff()
    .fillna(0)
)

df["vehicle_change"] = (
    group["vehicle_count"]
    .diff()
    .fillna(0)
)

df["stopped_change"] = (
    group["stopped_vehicles"]
    .diff()
    .fillna(0)
)

df["waiting_change"] = (
    group["average_waiting_time"]
    .diff()
    .fillna(0)
)

df["density_change"] = (
    group["density_veh_per_km"]
    .diff()
    .fillna(0)
)

df["queue_change"] = (
    group["queue_length_estimate_m"]
    .diff()
    .fillna(0)
)


# ============================================================
# MULTI-STEP CHANGES
# ============================================================

print(
    "Creating 5/15/30/60 second changes..."
)

for lag in [5, 15, 30, 60]:

    df[f"speed_change_{lag}s"] = (
        df["average_speed_kmh"]
        - group["average_speed_kmh"]
        .shift(lag)
    ).fillna(0)

    df[f"density_change_{lag}s"] = (
        df["density_veh_per_km"]
        - group["density_veh_per_km"]
        .shift(lag)
    ).fillna(0)

    df[f"queue_change_{lag}s"] = (
        df["queue_length_estimate_m"]
        - group["queue_length_estimate_m"]
        .shift(lag)
    ).fillna(0)

    df[f"waiting_change_{lag}s"] = (
        df["average_waiting_time"]
        - group["average_waiting_time"]
        .shift(lag)
    ).fillna(0)


# ============================================================
# ROLLING FEATURES
# ============================================================

print(
    "Creating rolling averages..."
)

for window in [15, 30, 60]:

    df[f"speed_mean_{window}s"] = (
        group["average_speed_kmh"]
        .transform(
            lambda x:
                x.rolling(
                    window,
                    min_periods=1
                ).mean()
        )
    )

    df[f"density_mean_{window}s"] = (
        group["density_veh_per_km"]
        .transform(
            lambda x:
                x.rolling(
                    window,
                    min_periods=1
                ).mean()
        )
    )

    df[f"queue_mean_{window}s"] = (
        group["queue_length_estimate_m"]
        .transform(
            lambda x:
                x.rolling(
                    window,
                    min_periods=1
                ).mean()
        )
    )

    df[f"waiting_mean_{window}s"] = (
        group["average_waiting_time"]
        .transform(
            lambda x:
                x.rolling(
                    window,
                    min_periods=1
                ).mean()
        )
    )


# ============================================================
# ACCELERATION / TREND
# ============================================================

print(
    "Creating acceleration features..."
)

df["speed_acceleration"] = (
    df["speed_change"]
    - group["speed_change"]
    .shift(1)
    .fillna(0)
)

df["density_acceleration"] = (
    df["density_change"]
    - group["density_change"]
    .shift(1)
    .fillna(0)
)

df["queue_acceleration"] = (
    df["queue_change"]
    - group["queue_change"]
    .shift(1)
    .fillna(0)
)


# ============================================================
# CONGESTION ENCODING
# ============================================================

congestion_map = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CONGESTED": 3
}

df["current_congestion_encoded"] = (
    df["congestion_level"]
    .map(congestion_map)
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
)


# ============================================================
# ROAD QUALITY FILTER
# ============================================================

print("""
========================================
 ROAD QUALITY FILTER
========================================
""")

before = len(df)

df = df[
    df["road_length_m"]
    >= MIN_ROAD_LENGTH_M
].copy()

print(
    f"Minimum road length: "
    f"{MIN_ROAD_LENGTH_M} m"
)

print(
    f"Rows removed: "
    f"{before - len(df):,}"
)

print(
    f"Rows retained: "
    f"{len(df):,}"
)


# ============================================================
# ACTIVE ROAD FILTER
# ============================================================

print("""
========================================
 ACTIVE ROAD FILTER
========================================
""")

before = len(df)

df = df[
    df["vehicle_count"] > 0
].copy()

print(
    f"Rows removed: "
    f"{before - len(df):,}"
)

print(
    f"Rows retained: "
    f"{len(df):,}"
)


# ============================================================
# FEATURE LIST
# ============================================================

feature_columns = [

    "road_length_m",

    "vehicle_count",

    "average_speed_kmh",

    "stopped_vehicles",

    "average_waiting_time",

    "density_veh_per_km",

    "queue_length_estimate_m",

    "current_congestion_encoded",

    "scenario_encoded",

    "speed_change",

    "vehicle_change",

    "stopped_change",

    "waiting_change",

    "density_change",

    "queue_change",

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

    "speed_acceleration",

    "density_acceleration",

    "queue_acceleration"
]


target_column = "future_congestion"


# ============================================================
# FINAL DATASET
# ============================================================

final_columns = (
    [
        "scenario",
        "step",
        "road_id"
    ]
    + feature_columns
    + [
        target_column
    ]
)

df = df[final_columns]


# ============================================================
# CLEAN
# ============================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.dropna()


# ============================================================
# SUMMARY
# ============================================================

print("""
========================================
 V3 DATASET SUMMARY
========================================
""")

print(
    f"Rows     : {len(df):,}"
)

print(
    f"Features : {len(feature_columns)}"
)

print(
    f"Columns  : {len(df.columns)}"
)

print(
    f"Roads    : {df['road_id'].nunique():,}"
)

print(
    f"Steps    : "
    f"{df['step'].min()} - "
    f"{df['step'].max()}"
)


print("""
========================================
 TARGET DISTRIBUTION
========================================
""")

print(
    df[target_column]
    .value_counts()
)

print("\nPercentage:")

print(
    df[target_column]
    .value_counts(
        normalize=True
    )
    .mul(100)
    .round(2)
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("""
========================================
 XGBOOST V3 DATASET CREATED
========================================
""")

print(
    f"Output:\n{OUTPUT_FILE}"
)