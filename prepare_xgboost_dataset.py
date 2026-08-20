import pandas as pd
import os

# ============================================================
# TRAFFICX - XGBOOST DATASET PREPARATION
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_ml_dataset.csv"
)

OUTPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_dataset.csv"
)


print("\n========================================")
print(" TRAFFICX - XGBOOST DATASET PREPARATION")
print("========================================")


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading ML dataset...")

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Input rows: {len(df):,}"
)


# ============================================================
# KEEP ROADS THAT CURRENTLY HAVE TRAFFIC
# ============================================================

df = df[
    df["vehicle_count"] > 0
].copy()


print("\n========================================")
print(" Active-road filtering")
print("========================================")

print(
    f"Rows retained: {len(df):,}"
)


# ============================================================
# REMOVE SCENARIO FROM ML FEATURES
# ============================================================
#
# Scenario is an artificial simulation label.
#
# The model should learn traffic conditions from
# measurable road-level variables instead.
#
# We retain scenario temporarily for analysis/splitting.
# ============================================================


# ============================================================
# FEATURE COLUMNS
# ============================================================

features = [
    "road_id",
    "road_length_m",
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m"
]


target = "future_congestion"


# ============================================================
# KEEP REQUIRED COLUMNS
# ============================================================

columns = (
    [
        "scenario",
        "step"
    ]
    +
    features
    +
    [
        target
    ]
)

df = df[columns]


# ============================================================
# REMOVE INVALID TARGETS
# ============================================================

df = df.dropna(
    subset=[target]
).copy()


# ============================================================
# DISPLAY TARGET DISTRIBUTION
# ============================================================

print("\n========================================")
print(" TARGET DISTRIBUTION")
print("========================================")

counts = df[target].value_counts()

print(counts)

print("\nPercentage:")

percentages = (
    df[target]
    .value_counts(
        normalize=True
    )
    .mul(100)
    .round(2)
)

print(percentages)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n========================================")
print(" XGBOOST DATASET READY")
print("========================================")

print(
    f"Output: {OUTPUT_FILE}"
)

print(
    f"Rows: {len(df):,}"
)

print(
    f"Features: {len(features)}"
)

print(
    f"Target: {target}"
)

print("\nFeatures:")

for feature in features:

    print(
        f"  - {feature}"
    )

print("\n========================================")