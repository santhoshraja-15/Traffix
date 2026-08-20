import pandas as pd

# ============================================================
# TRAFFICX - Future Congestion Target Generator
# ============================================================

INPUT_FILE = r"D:\TRAFFICX\road_level_features.csv"
OUTPUT_FILE = r"D:\TRAFFICX\prediction_dataset_5min.csv"

# SUMO is currently collecting one record per simulation step.
# 5 minutes = 300 simulation steps.
FUTURE_STEPS = 300

print("\n========================================")
print(" TRAFFICX - FUTURE CONGESTION TARGET")
print("========================================")

# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"Input rows: {len(df):,}")
print(f"Unique roads: {df['road_id'].nunique():,}")

# ------------------------------------------------------------
# Make sure data is sorted correctly
# ------------------------------------------------------------

df = df.sort_values(
    ["road_id", "step"]
).reset_index(drop=True)

# ------------------------------------------------------------
# Create lookup table
# ------------------------------------------------------------

future = df[
    [
        "road_id",
        "step",
        "congestion_level",
        "average_speed_kmh",
        "vehicle_count"
    ]
].copy()

# The future record occurs 300 simulation steps later.
future["step"] = future["step"] - FUTURE_STEPS

future = future.rename(
    columns={
        "congestion_level": "future_congestion",
        "average_speed_kmh": "future_speed_kmh",
        "vehicle_count": "future_vehicle_count"
    }
)

# ------------------------------------------------------------
# Match:
#
# current road_id + current step
#
# with:
#
# same road_id + current step + 300
# ------------------------------------------------------------

df = df.merge(
    future,
    on=["road_id", "step"],
    how="left"
)

# ------------------------------------------------------------
# Remove rows where a 5-minute future value doesn't exist
# ------------------------------------------------------------

before = len(df)

df = df.dropna(
    subset=["future_congestion"]
).copy()

after = len(df)

print(
    f"\nRows with 5-minute future target: "
    f"{after:,}"
)

print(
    f"Rows removed because future data "
    f"was unavailable: {before - after:,}"
)

# ------------------------------------------------------------
# Save prediction dataset
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ------------------------------------------------------------
# Display target distribution
# ------------------------------------------------------------

print("\nFuture congestion distribution:")

print(
    df["future_congestion"]
    .value_counts()
)

print("\nFuture congestion percentage:")

print(
    (
        df["future_congestion"]
        .value_counts(normalize=True)
        * 100
    ).round(2)
)

# ------------------------------------------------------------
# Show sample
# ------------------------------------------------------------

print("\nSample prediction records:")

print(
    df[
        [
            "road_id",
            "step",
            "congestion_level",
            "future_congestion",
            "average_speed_kmh",
            "future_speed_kmh",
            "vehicle_count",
            "future_vehicle_count"
        ]
    ].head(15).to_string(index=False)
)

print("\n========================================")
print(" Prediction dataset created")
print(f" Output: {OUTPUT_FILE}")
print(" Prediction horizon: 5 minutes")
print("========================================")