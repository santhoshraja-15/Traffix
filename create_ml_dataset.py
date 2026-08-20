import os
import sys
import pandas as pd
import numpy as np


# ============================================================
# TRAFFICX - ML DATASET V2
# ACTIVITY-AWARE + TEMPORAL FEATURE ENGINEERING
# ============================================================

print("\n" + "=" * 60)
print(" TRAFFICX - ML DATASET V2")
print(" ACTIVITY-AWARE + TEMPORAL FEATURE ENGINEERING")
print("=" * 60)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"D:\TRAFFICX\road_datasets"

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "trafficx_ml_dataset_v2.csv"
)

FUTURE_STEPS = 10

RAW_FILES = {
    "low": os.path.join(BASE_DIR, "road_low.csv"),
    "medium": os.path.join(BASE_DIR, "road_medium.csv"),
    "high": os.path.join(BASE_DIR, "road_high.csv"),
    "congested": os.path.join(BASE_DIR, "road_congested.csv"),
}


print("\nDataset directory:")
print(BASE_DIR)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nFuture prediction horizon:")
print(f"{FUTURE_STEPS} simulation steps")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def find_column(df, candidates, required=True):
    """
    Find a column using a list of possible names.
    Matching is case-insensitive.
    """

    lower_map = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:

        key = candidate.strip().lower()

        if key in lower_map:
            return lower_map[key]

    if required:
        raise RuntimeError(
            "\nRequired column not found.\n"
            f"Tried: {candidates}\n"
            f"Available columns:\n{list(df.columns)}"
        )

    return None


def classify_congestion(row):

    vehicles = row["vehicle_count"]
    speed = row["average_speed_kmh"]
    stopped = row["stopped_vehicles"]

    # --------------------------------------------------------
    # No active vehicles
    # --------------------------------------------------------

    if vehicles <= 0:
        return "LOW"

    # --------------------------------------------------------
    # Strong congestion indicators
    # --------------------------------------------------------

    if speed < 15:
        return "CONGESTED"

    if stopped > 0 and speed < 25:
        return "CONGESTED"

    # --------------------------------------------------------
    # High congestion
    # --------------------------------------------------------

    if speed < 30:
        return "HIGH"

    # --------------------------------------------------------
    # Medium congestion
    # --------------------------------------------------------

    if speed < 45:
        return "MEDIUM"

    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    return "LOW"


def classify_future(row):

    vehicles = row["future_vehicle_count"]
    speed = row["future_speed_kmh"]
    stopped = row["future_stopped_vehicles"]

    if pd.isna(speed):
        return None

    if pd.isna(vehicles):
        return None

    # --------------------------------------------------------
    # No future traffic
    # --------------------------------------------------------

    if vehicles <= 0:
        return "LOW"

    # --------------------------------------------------------
    # Future severe congestion
    # --------------------------------------------------------

    if speed < 15:
        return "CONGESTED"

    if stopped > 0 and speed < 25:
        return "CONGESTED"

    # --------------------------------------------------------
    # Future high congestion
    # --------------------------------------------------------

    if speed < 30:
        return "HIGH"

    # --------------------------------------------------------
    # Future medium congestion
    # --------------------------------------------------------

    if speed < 45:
        return "MEDIUM"

    return "LOW"


# ============================================================
# LOAD RAW SUMO DATA
# ============================================================

print("\n" + "=" * 60)
print(" LOADING RAW SUMO DATA")
print("=" * 60)


frames = []


for scenario, file_path in RAW_FILES.items():

    print(f"\nChecking: {file_path}")

    if not os.path.exists(file_path):

        print("  WARNING: File not found")

        continue

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    print(f"  Size: {file_size_mb:.2f} MB")

    print("  Loading...")

    try:

        temp = pd.read_csv(file_path)

    except Exception as e:

        print(f"  ERROR loading file: {e}")

        continue

    print(f"  Rows: {len(temp):,}")

    print(f"  Columns: {len(temp.columns)}")

    print(f"  Columns: {list(temp.columns)}")

    temp["scenario"] = scenario

    frames.append(temp)


if len(frames) == 0:

    raise RuntimeError(
        "\nNo road scenario CSV files were found.\n\n"
        "Expected files:\n"
        "  road_low.csv\n"
        "  road_medium.csv\n"
        "  road_high.csv\n"
        "  road_congested.csv\n\n"
        f"Expected directory:\n{BASE_DIR}"
    )


# ============================================================
# COMBINE
# ============================================================

print("\n" + "=" * 60)
print(" COMBINING SCENARIOS")
print("=" * 60)


df = pd.concat(
    frames,
    ignore_index=True
)


print(f"\nCombined rows: {len(df):,}")


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

df.columns = [
    str(c).strip()
    for c in df.columns
]


# ============================================================
# IDENTIFY REQUIRED COLUMNS
# ============================================================

print("\n" + "=" * 60)
print(" IDENTIFYING RAW COLUMNS")
print("=" * 60)


step_col = find_column(
    df,
    [
        "step",
        "simulation_step",
        "time_step",
        "t"
    ]
)


road_col = find_column(
    df,
    [
        "road_id",
        "edge_id",
        "edge",
        "road",
        "id"
    ]
)


length_col = find_column(
    df,
    [
        "road_length_m",
        "road_length",
        "length_m",
        "length"
    ]
)


vehicle_col = find_column(
    df,
    [
        "vehicle_count",
        "vehicles",
        "vehicle_number",
        "num_vehicles",
        "count"
    ]
)


speed_col = find_column(
    df,
    [
        "average_speed_kmh",
        "avg_speed_kmh",
        "average_speed",
        "avg_speed",
        "speed_kmh"
    ]
)


stopped_col = find_column(
    df,
    [
        "stopped_vehicles",
        "stopped",
        "halted_vehicles",
        "waiting_vehicles"
    ]
)


waiting_col = find_column(
    df,
    [
        "average_waiting_time",
        "avg_waiting_time",
        "waiting_time",
        "avg_wait"
    ]
)


density_col = find_column(
    df,
    [
        "density_veh_per_km",
        "density",
        "vehicle_density",
        "density_vehicles_per_km"
    ]
)


queue_col = find_column(
    df,
    [
        "queue_length_estimate_m",
        "queue_length_m",
        "queue_length",
        "estimated_queue_length_m"
    ]
)


print("\nDetected columns:")

print(f"  Step              : {step_col}")
print(f"  Road ID           : {road_col}")
print(f"  Road length       : {length_col}")
print(f"  Vehicle count     : {vehicle_col}")
print(f"  Average speed     : {speed_col}")
print(f"  Stopped vehicles  : {stopped_col}")
print(f"  Waiting time      : {waiting_col}")
print(f"  Density           : {density_col}")
print(f"  Queue length      : {queue_col}")


# ============================================================
# STANDARDIZE COLUMN NAMES
# ============================================================

df = df.rename(
    columns={
        step_col: "step",
        road_col: "road_id",
        length_col: "road_length_m",
        vehicle_col: "vehicle_count",
        speed_col: "average_speed_kmh",
        stopped_col: "stopped_vehicles",
        waiting_col: "average_waiting_time",
        density_col: "density_veh_per_km",
        queue_col: "queue_length_estimate_m",
    }
)


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "step",
    "road_length_m",
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m"
]


for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

before_invalid = len(df)


df = df.dropna(
    subset=numeric_columns
).copy()


print("\nInvalid rows removed:")
print(
    f"{before_invalid - len(df):,}"
)


# ============================================================
# SORT TEMPORALLY
# ============================================================

print("\n" + "=" * 60)
print(" SORTING TEMPORAL DATA")
print("=" * 60)


df = df.sort_values(
    [
        "scenario",
        "road_id",
        "step"
    ]
).reset_index(drop=True)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

duplicates = df.duplicated(
    subset=[
        "scenario",
        "road_id",
        "step"
    ]
).sum()


print(f"\nDuplicate scenario/road/step rows: {duplicates:,}")


if duplicates > 0:

    df = df.drop_duplicates(
        subset=[
            "scenario",
            "road_id",
            "step"
        ],
        keep="first"
    ).copy()


# ============================================================
# CURRENT CONGESTION
# ============================================================

print("\n" + "=" * 60)
print(" CREATING CURRENT CONGESTION")
print("=" * 60)


df["congestion_level"] = df.apply(
    classify_congestion,
    axis=1
)


print(
    df["congestion_level"]
    .value_counts()
    .to_string()
)


# ============================================================
# ACTIVITY FEATURES
# ============================================================

print("\n" + "=" * 60)
print(" CREATING ACTIVITY FEATURES")
print("=" * 60)


# Vehicle presence

df["has_vehicles"] = (
    df["vehicle_count"] > 0
).astype("int8")


# Stopped vehicle presence

df["has_stopped_vehicles"] = (
    df["stopped_vehicles"] > 0
).astype("int8")


# Queue presence

df["has_queue"] = (
    df["queue_length_estimate_m"] > 0
).astype("int8")


# Traffic activity ratio

df["stopped_vehicle_ratio"] = np.where(
    df["vehicle_count"] > 0,

    df["stopped_vehicles"] /
    df["vehicle_count"],

    0.0
)


# ============================================================
# CURRENT NORMALIZED FEATURES
# ============================================================

df["vehicles_per_100m"] = np.where(
    df["road_length_m"] > 0,

    df["vehicle_count"] /
    df["road_length_m"] *
    100,

    0.0
)


df["queue_ratio"] = np.where(
    df["road_length_m"] > 0,

    df["queue_length_estimate_m"] /
    df["road_length_m"],

    0.0
)


# ============================================================
# TEMPORAL FEATURES
# ============================================================

print("\n" + "=" * 60)
print(" CREATING TEMPORAL FEATURES")
print("=" * 60)


group_columns = [
    "scenario",
    "road_id"
]


# ------------------------------------------------------------
# Previous values
# ------------------------------------------------------------

df["previous_speed_kmh"] = (
    df.groupby(group_columns)[
        "average_speed_kmh"
    ]
    .shift(1)
)


df["previous_vehicle_count"] = (
    df.groupby(group_columns)[
        "vehicle_count"
    ]
    .shift(1)
)


df["previous_density"] = (
    df.groupby(group_columns)[
        "density_veh_per_km"
    ]
    .shift(1)
)


df["previous_queue_length_m"] = (
    df.groupby(group_columns)[
        "queue_length_estimate_m"
    ]
    .shift(1)
)


# ------------------------------------------------------------
# Change features
# ------------------------------------------------------------

df["speed_change_kmh"] = (
    df["average_speed_kmh"] -
    df["previous_speed_kmh"]
)


df["vehicle_change"] = (
    df["vehicle_count"] -
    df["previous_vehicle_count"]
)


df["density_change"] = (
    df["density_veh_per_km"] -
    df["previous_density"]
)


df["queue_change_m"] = (
    df["queue_length_estimate_m"] -
    df["previous_queue_length_m"]
)


# ------------------------------------------------------------
# Percentage changes
# ------------------------------------------------------------

df["speed_change_pct"] = np.where(
    df["previous_speed_kmh"] > 0,

    (
        (
            df["average_speed_kmh"] -
            df["previous_speed_kmh"]
        )
        /
        df["previous_speed_kmh"]
    ) * 100,

    0.0
)


df["vehicle_change_pct"] = np.where(
    df["previous_vehicle_count"] > 0,

    (
        (
            df["vehicle_count"] -
            df["previous_vehicle_count"]
        )
        /
        df["previous_vehicle_count"]
    ) * 100,

    0.0
)


# ============================================================
# FILL FIRST TEMPORAL ROWS
# ============================================================

temporal_columns = [
    "previous_speed_kmh",
    "previous_vehicle_count",
    "previous_density",
    "previous_queue_length_m",
    "speed_change_kmh",
    "vehicle_change",
    "density_change",
    "queue_change_m",
    "speed_change_pct",
    "vehicle_change_pct"
]


for col in temporal_columns:

    df[col] = df[col].replace(
        [np.inf, -np.inf],
        np.nan
    )

    df[col] = df[col].fillna(0)


# ============================================================
# CREATE FUTURE FEATURES
# ============================================================

print("\n" + "=" * 60)
print(" CREATING FUTURE FEATURES")
print("=" * 60)


df["future_speed_kmh"] = (
    df.groupby(group_columns)[
        "average_speed_kmh"
    ]
    .shift(-FUTURE_STEPS)
)


df["future_vehicle_count"] = (
    df.groupby(group_columns)[
        "vehicle_count"
    ]
    .shift(-FUTURE_STEPS)
)


df["future_density"] = (
    df.groupby(group_columns)[
        "density_veh_per_km"
    ]
    .shift(-FUTURE_STEPS)
)


df["future_waiting_time"] = (
    df.groupby(group_columns)[
        "average_waiting_time"
    ]
    .shift(-FUTURE_STEPS)
)


df["future_queue_length"] = (
    df.groupby(group_columns)[
        "queue_length_estimate_m"
    ]
    .shift(-FUTURE_STEPS)
)


df["future_stopped_vehicles"] = (
    df.groupby(group_columns)[
        "stopped_vehicles"
    ]
    .shift(-FUTURE_STEPS)
)


# ============================================================
# FUTURE TARGET
# ============================================================

print("\n" + "=" * 60)
print(" CREATING FUTURE CONGESTION TARGET")
print("=" * 60)


df["future_congestion"] = df.apply(
    classify_future,
    axis=1
)


# ============================================================
# REMOVE ROWS WITHOUT FUTURE TARGET
# ============================================================

before = len(df)


df = df.dropna(
    subset=[
        "future_speed_kmh",
        "future_vehicle_count",
        "future_density",
        "future_waiting_time",
        "future_queue_length",
        "future_stopped_vehicles",
        "future_congestion"
    ]
).copy()


after = len(df)


print("\nRows before future target removal:")
print(f"{before:,}")


print("\nRows retained:")
print(f"{after:,}")


print("\nRows removed:")
print(f"{before - after:,}")


# ============================================================
# FUTURE ACTIVITY FEATURES
# ============================================================

df["future_has_vehicles"] = (
    df["future_vehicle_count"] > 0
).astype("int8")


df["future_has_stopped_vehicles"] = (
    df["future_stopped_vehicles"] > 0
).astype("int8")


# ============================================================
# TEMPORAL TARGET CHANGES
# ============================================================

df["future_speed_delta"] = (
    df["future_speed_kmh"] -
    df["average_speed_kmh"]
)


df["future_vehicle_delta"] = (
    df["future_vehicle_count"] -
    df["vehicle_count"]
)


df["future_density_delta"] = (
    df["future_density"] -
    df["density_veh_per_km"]
)


df["future_queue_delta"] = (
    df["future_queue_length"] -
    df["queue_length_estimate_m"]
)


# ============================================================
# FINAL FEATURE / TARGET STRUCTURE
# ============================================================

feature_columns = [

    # --------------------------------------------------------
    # Identity / temporal
    # --------------------------------------------------------

    "scenario",
    "step",
    "road_id",

    # --------------------------------------------------------
    # Road
    # --------------------------------------------------------

    "road_length_m",

    # --------------------------------------------------------
    # Current traffic
    # --------------------------------------------------------

    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",

    # --------------------------------------------------------
    # Current activity
    # --------------------------------------------------------

    "has_vehicles",
    "has_stopped_vehicles",
    "has_queue",
    "stopped_vehicle_ratio",

    # --------------------------------------------------------
    # Normalized
    # --------------------------------------------------------

    "vehicles_per_100m",
    "queue_ratio",

    # --------------------------------------------------------
    # Current congestion
    # --------------------------------------------------------

    "congestion_level",

    # --------------------------------------------------------
    # Temporal
    # --------------------------------------------------------

    "previous_speed_kmh",
    "previous_vehicle_count",
    "previous_density",
    "previous_queue_length_m",

    "speed_change_kmh",
    "vehicle_change",
    "density_change",
    "queue_change_m",

    "speed_change_pct",
    "vehicle_change_pct",
]


target_columns = [

    # --------------------------------------------------------
    # Future numerical targets
    # --------------------------------------------------------

    "future_speed_kmh",
    "future_vehicle_count",
    "future_density",
    "future_waiting_time",
    "future_queue_length",
    "future_stopped_vehicles",

    # --------------------------------------------------------
    # Future activity
    # --------------------------------------------------------

    "future_has_vehicles",
    "future_has_stopped_vehicles",

    # --------------------------------------------------------
    # Future deltas
    # --------------------------------------------------------

    "future_speed_delta",
    "future_vehicle_delta",
    "future_density_delta",
    "future_queue_delta",

    # --------------------------------------------------------
    # Main classification target
    # --------------------------------------------------------

    "future_congestion",
]


final_columns = (
    feature_columns +
    target_columns
)


df = df[final_columns].copy()


# ============================================================
# CLEAN NUMERIC VALUES
# ============================================================

numeric_final_columns = df.select_dtypes(
    include=[np.number]
).columns


for col in numeric_final_columns:

    df[col] = df[col].replace(
        [np.inf, -np.inf],
        np.nan
    )


# Drop unexpected numerical NaNs

df = df.dropna(
    subset=numeric_final_columns
).copy()


# ============================================================
# FINAL SORT
# ============================================================

df = df.sort_values(
    [
        "scenario",
        "road_id",
        "step"
    ]
).reset_index(drop=True)


# ============================================================
# DATASET SUMMARY
# ============================================================

print("\n" + "=" * 60)
print(" FINAL DATASET SUMMARY")
print("=" * 60)


print("\nShape:")
print(df.shape)


print("\nRows:")
print(f"{len(df):,}")


print("\nColumns:")
print(len(df.columns))


# ============================================================
# CURRENT DISTRIBUTION
# ============================================================

print("\n" + "=" * 60)
print(" CURRENT CONGESTION DISTRIBUTION")
print("=" * 60)


print(
    df["congestion_level"]
    .value_counts()
    .to_string()
)


print("\nPercentages:")


current_pct = (
    df["congestion_level"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


print(current_pct.to_string())


# ============================================================
# FUTURE DISTRIBUTION
# ============================================================

print("\n" + "=" * 60)
print(" FUTURE CONGESTION DISTRIBUTION")
print("=" * 60)


print(
    df["future_congestion"]
    .value_counts()
    .to_string()
)


print("\nPercentages:")


future_pct = (
    df["future_congestion"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


print(future_pct.to_string())


# ============================================================
# FUTURE DISTRIBUTION BY SCENARIO
# ============================================================

print("\n" + "=" * 60)
print(" FUTURE CONGESTION BY SCENARIO")
print("=" * 60)


future_crosstab = pd.crosstab(
    df["scenario"],
    df["future_congestion"]
)


print("\nCounts:")
print(
    future_crosstab.to_string()
)


print("\nPercentages:")


future_scenario_pct = (
    pd.crosstab(
        df["scenario"],
        df["future_congestion"],
        normalize="index"
    )
    .mul(100)
    .round(2)
)


print(
    future_scenario_pct.to_string()
)


# ============================================================
# ACTIVITY BY SCENARIO
# ============================================================

print("\n" + "=" * 60)
print(" ACTIVITY BY SCENARIO")
print("=" * 60)


activity = df.groupby(
    "scenario"
).agg(

    total=(
        "vehicle_count",
        "size"
    ),

    active=(
        "vehicle_count",
        lambda s: (s > 0).sum()
    ),

    stopped=(
        "stopped_vehicles",
        lambda s: (s > 0).sum()
    ),

    queued=(
        "queue_length_estimate_m",
        lambda s: (s > 0).sum()
    ),

    future_active=(
        "future_vehicle_count",
        lambda s: (s > 0).sum()
    )
)


activity["active_pct"] = (
    activity["active"] /
    activity["total"] *
    100
)


activity["stopped_pct"] = (
    activity["stopped"] /
    activity["total"] *
    100
)


activity["queued_pct"] = (
    activity["queued"] /
    activity["total"] *
    100
)


activity["future_active_pct"] = (
    activity["future_active"] /
    activity["total"] *
    100
)


print(
    activity.round(3).to_string()
)


# ============================================================
# NUMERICAL STATISTICS
# ============================================================

print("\n" + "=" * 60)
print(" ACTIVE-TRAFFIC STATISTICS")
print("=" * 60)


active_df = df[
    df["vehicle_count"] > 0
]


stats_columns = [
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m"
]


if len(active_df) > 0:

    stats = (
        active_df
        .groupby("scenario")[stats_columns]
        .agg(
            [
                "count",
                "mean",
                "median"
            ]
        )
        .round(2)
    )

    print(
        stats.to_string()
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

print("\n" + "=" * 60)
print(" DUPLICATE CHECK")
print("=" * 60)


duplicate_count = df.duplicated(
    subset=[
        "scenario",
        "road_id",
        "step"
    ]
).sum()


print(
    f"Duplicate scenario/road/step rows: "
    f"{duplicate_count:,}"
)


# ============================================================
# NULL CHECK
# ============================================================

print("\n" + "=" * 60)
print(" NULL CHECK")
print("=" * 60)


null_counts = df.isna().sum()


null_counts = null_counts[
    null_counts > 0
]


if len(null_counts) == 0:

    print("No NULL values found.")

else:

    print(
        null_counts.to_string()
    )


# ============================================================
# DATASET SIZE
# ============================================================

estimated_memory_mb = (
    df.memory_usage(
        deep=True
    ).sum()
    /
    (1024 * 1024)
)


print("\nEstimated in-memory size:")
print(
    f"{estimated_memory_mb:.2f} MB"
)


# ============================================================
# SAVE
# ============================================================

print("\n" + "=" * 60)
print(" SAVING DATASET")
print("=" * 60)


print(
    f"\nWriting:\n{OUTPUT_FILE}"
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


if not os.path.exists(OUTPUT_FILE):

    raise RuntimeError(
        "Dataset save failed."
    )


output_size_mb = (
    os.path.getsize(OUTPUT_FILE)
    /
    (1024 * 1024)
)


print("\nOutput file size:")
print(
    f"{output_size_mb:.2f} MB"
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 60)
print(" FINAL VALIDATION")
print("=" * 60)


required_final_columns = (
    feature_columns +
    target_columns
)


missing_columns = [
    c
    for c in required_final_columns
    if c not in df.columns
]


if missing_columns:

    print("\nERROR: Missing columns:")

    for col in missing_columns:
        print(f"  {col}")

    sys.exit(1)


print("\nAll expected columns present.")


if df["future_congestion"].isna().sum() != 0:

    print(
        "ERROR: Future target contains NULL values."
    )

    sys.exit(1)


if df.duplicated(
    subset=[
        "scenario",
        "road_id",
        "step"
    ]
).sum() != 0:

    print(
        "ERROR: Duplicate scenario/road/step rows found."
    )

    sys.exit(1)


print("\nDataset validation PASSED.")


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 60)
print(" DATASET CREATION COMPLETE")
print("=" * 60)


print(
    f"\nFinal dataset:"
)


print(
    OUTPUT_FILE
)


print(
    f"\nFinal shape: {df.shape}"
)


print("\nReady for ML training.")
print()