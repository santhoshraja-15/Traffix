import pandas as pd
import os

# ============================================================
# TRAFFICX - Road Scenario Validation
# ============================================================

BASE_DIR = r"D:\TRAFFICX\road_datasets"

SCENARIOS = [
    "low",
    "medium",
    "high",
    "congested"
]

print("\n========================================")
print(" TRAFFICX - ROAD SCENARIO VALIDATION")
print("========================================")

results = []

for scenario in SCENARIOS:

    file_path = os.path.join(
        BASE_DIR,
        f"road_{scenario}.csv"
    )

    print(f"\nLoading {scenario.upper()}...")

    df = pd.read_csv(file_path)

    # --------------------------------------------------------
    # Basic statistics
    # --------------------------------------------------------

    avg_vehicles = df["vehicle_count"].mean()

    avg_speed = df[
        df["vehicle_count"] > 0
    ]["average_speed_kmh"].mean()

    avg_waiting = df[
        df["vehicle_count"] > 0
    ]["average_waiting_time"].mean()

    avg_density = df[
        df["vehicle_count"] > 0
    ]["density_veh_per_km"].mean()

    avg_queue = df[
        df["vehicle_count"] > 0
    ]["queue_length_estimate_m"].mean()

    max_vehicles = df["vehicle_count"].max()

    total_rows = len(df)

    unique_roads = df["road_id"].nunique()

    # --------------------------------------------------------
    # Store results
    # --------------------------------------------------------

    results.append({
        "scenario": scenario.upper(),
        "rows": total_rows,
        "unique_roads": unique_roads,
        "avg_vehicles": avg_vehicles,
        "avg_speed_kmh": avg_speed,
        "avg_waiting_s": avg_waiting,
        "avg_density": avg_density,
        "avg_queue_m": avg_queue,
        "max_vehicles": max_vehicles
    })


# ============================================================
# Results table
# ============================================================

result_df = pd.DataFrame(results)

print("\n========================================")
print(" SCENARIO COMPARISON")
print("========================================")

print(
    result_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.2f}"
    )
)


# ============================================================
# Check expected trend
# ============================================================

print("\n========================================")
print(" EXPECTED TRAFFIC TREND")
print("========================================")

print(
    "Vehicle count should generally increase:"
)

print(
    result_df[
        ["scenario", "avg_vehicles"]
    ].to_string(index=False)
)

print(
    "\nSpeed should generally decrease:"
)

print(
    result_df[
        ["scenario", "avg_speed_kmh"]
    ].to_string(index=False)
)

print(
    "\nWaiting time should generally increase:"
)

print(
    result_df[
        ["scenario", "avg_waiting_s"]
    ].to_string(index=False)
)


# ============================================================
# Save validation report
# ============================================================

output_file = os.path.join(
    BASE_DIR,
    "scenario_validation.csv"
)

result_df.to_csv(
    output_file,
    index=False
)

print("\n========================================")
print(" Validation complete")
print(f" Report: {output_file}")
print("========================================")