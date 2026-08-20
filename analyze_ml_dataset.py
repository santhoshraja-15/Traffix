import pandas as pd

INPUT_FILE = r"D:\TRAFFICX\road_datasets\trafficx_ml_dataset.csv"

print("\n========================================")
print(" TRAFFICX - ML DATASET ANALYSIS")
print("========================================")

df = pd.read_csv(INPUT_FILE)

print(f"\nTotal rows: {len(df):,}")

print(
    f"Unique roads: {df['road_id'].nunique():,}"
)

print(
    f"Scenarios: {df['scenario'].nunique()}"
)


# ============================================================
# CURRENT VEHICLE STATUS
# ============================================================

zero_current = (
    df["vehicle_count"] == 0
).sum()

active_current = (
    df["vehicle_count"] > 0
).sum()


print("\n========================================")
print(" CURRENT ROAD ACTIVITY")
print("========================================")

print(
    f"Zero vehicles : {zero_current:,}"
)

print(
    f"Active roads  : {active_current:,}"
)

print(
    f"Zero percentage : "
    f"{zero_current / len(df) * 100:.2f}%"
)

print(
    f"Active percentage : "
    f"{active_current / len(df) * 100:.2f}%"
)


# ============================================================
# FUTURE VEHICLE STATUS
# ============================================================

zero_future = (
    df["future_vehicle_count"] == 0
).sum()

active_future = (
    df["future_vehicle_count"] > 0
).sum()


print("\n========================================")
print(" FUTURE ROAD ACTIVITY")
print("========================================")

print(
    f"Future zero vehicles : {zero_future:,}"
)

print(
    f"Future active roads  : {active_future:,}"
)


# ============================================================
# ACTIVE NOW OR IN FUTURE
# ============================================================

active_now_or_future = (
    (df["vehicle_count"] > 0) |
    (df["future_vehicle_count"] > 0)
)

print("\n========================================")
print(" ACTIVE NOW OR FUTURE")
print("========================================")

print(
    f"Rows: "
    f"{active_now_or_future.sum():,}"
)

print(
    f"Percentage: "
    f"{active_now_or_future.mean() * 100:.2f}%"
)


# ============================================================
# CURRENT CONGESTION
# ============================================================

print("\n========================================")
print(" CURRENT CONGESTION")
print("========================================")

print(
    df["congestion_level"].value_counts()
)

print("\nPercentage:")

print(
    df["congestion_level"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ============================================================
# FUTURE CONGESTION
# ============================================================

print("\n========================================")
print(" FUTURE CONGESTION")
print("========================================")

print(
    df["future_congestion"].value_counts()
)

print("\nPercentage:")

print(
    df["future_congestion"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ============================================================
# FUTURE CONGESTION - ACTIVE ROADS ONLY
# ============================================================

active_df = df[
    (df["vehicle_count"] > 0) |
    (df["future_vehicle_count"] > 0)
].copy()


print("\n========================================")
print(" FUTURE CONGESTION - ACTIVE ROADS")
print("========================================")

print(
    active_df["future_congestion"].value_counts()
)

print("\nPercentage:")

print(
    active_df["future_congestion"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


print("\n========================================")
print(" Analysis complete")
print("========================================")