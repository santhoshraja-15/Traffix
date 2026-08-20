import os
import sys
import time
import math
import numpy as np
import pandas as pd
import xgboost as xgb

# ============================================================
# TRAFFICX V15 - LIVE SUMO RISK PREDICTION
# ============================================================

SUMO_HOME = os.environ.get("SUMO_HOME")

if not SUMO_HOME:
    print("ERROR: SUMO_HOME environment variable is not set.")
    sys.exit(1)

sys.path.append(os.path.join(SUMO_HOME, "tools"))

import traci


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = (
    r"D:\TRAFFICX\models"
    r"\trafficx_xgboost_v15_risk_escalation.json"
)

SCENARIO = "medium"

SUMO_CONFIG = (
    rf"D:\TRAFFICX\scenarios\{SCENARIO}\traffic.sumocfg"
)

THRESHOLD = 0.96

SUMO_BINARY = "sumo"

# Run a fixed number of simulation steps.
# This prevents SUMO from ending before we see live predictions.
MAX_STEPS = 1200

# Print detailed prediction output every N steps.
PRINT_INTERVAL = 10

# Save live predictions here.
OUTPUT_FILE = (
    rf"D:\TRAFFICX\models"
    rf"\trafficx_v15_live_predictions_{SCENARIO}.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print(" TRAFFICX V15 - LIVE RISK PREDICTION")
print("=" * 70)

print()
print("Model:")
print(MODEL_PATH)

print()
print("Scenario:")
print(SCENARIO)

print()
print("SUMO config:")
print(SUMO_CONFIG)

print()
print("Threshold:", THRESHOLD)

print()
print("Maximum simulation steps:", MAX_STEPS)


# ============================================================
# LOAD MODEL
# ============================================================

try:

    model = xgb.XGBClassifier()

    model.load_model(MODEL_PATH)

except Exception as e:

    print()
    print("ERROR: Could not load V15 model.")
    print(e)
    sys.exit(1)


print()
print("V15 model loaded successfully.")


# ============================================================
# FEATURE STATE
# ============================================================

previous = {}


# ============================================================
# LIVE OUTPUT STORAGE
# ============================================================

all_predictions = []


# ============================================================
# SAFE DIVISION
# ============================================================

def safe_div(a, b):

    if b is None or b == 0:
        return 0.0

    return float(a) / float(b)


# ============================================================
# GET ROAD LENGTH
# ============================================================

def get_road_length(edge_id):

    try:

        lane_count = traci.edge.getLaneNumber(edge_id)

        if lane_count > 0:

            # SUMO lane IDs are constructed as:
            #
            # edge_id_0
            # edge_id_1
            # ...

            lane_id = f"{edge_id}_0"

            length = traci.lane.getLength(lane_id)

            if length > 0:
                return float(length)

    except Exception:
        pass

    # Fallback
    return 100.0


# ============================================================
# COLLECT ROAD FEATURES
# ============================================================

def collect_edge_features(edge_id):

    vehicle_ids = traci.edge.getLastStepVehicleIDs(
        edge_id
    )

    vehicle_count = len(vehicle_ids)

    # --------------------------------------------------------
    # VEHICLE FEATURES
    # --------------------------------------------------------

    if vehicle_count == 0:

        average_speed_kmh = 0.0

        stopped_vehicles = 0

        average_waiting_time = 0.0

    else:

        speeds = []

        waiting_times = []

        stopped_vehicles = 0

        for veh_id in vehicle_ids:

            try:

                speed = traci.vehicle.getSpeed(
                    veh_id
                )

                waiting = (
                    traci.vehicle
                    .getAccumulatedWaitingTime(
                        veh_id
                    )
                )

                speeds.append(speed)

                waiting_times.append(waiting)

                if speed < 0.1:

                    stopped_vehicles += 1

            except Exception:

                continue

        if speeds:

            average_speed_kmh = (
                np.mean(speeds) * 3.6
            )

        else:

            average_speed_kmh = 0.0

        if waiting_times:

            average_waiting_time = (
                np.mean(waiting_times)
            )

        else:

            average_waiting_time = 0.0

    # --------------------------------------------------------
    # ROAD LENGTH
    # --------------------------------------------------------

    road_length_m = get_road_length(
        edge_id
    )

    if road_length_m <= 0:

        road_length_m = 100.0

    road_length_km = (
        road_length_m / 1000.0
    )

    # --------------------------------------------------------
    # DENSITY
    # --------------------------------------------------------

    density_veh_per_km = safe_div(
        vehicle_count,
        road_length_km
    )

    vehicles_per_100m = safe_div(
        vehicle_count,
        road_length_m / 100.0
    )

    # --------------------------------------------------------
    # QUEUE
    # --------------------------------------------------------

    queue_length_estimate_m = (
        stopped_vehicles * 7.5
    )

    queue_ratio = safe_div(
        queue_length_estimate_m,
        road_length_m
    )

    # --------------------------------------------------------
    # PREVIOUS STATE
    # --------------------------------------------------------

    if edge_id not in previous:

        prev = {

            "speed":
                average_speed_kmh,

            "vehicles":
                vehicle_count,

            "density":
                density_veh_per_km,

            "queue":
                queue_length_estimate_m,

            "stopped":
                stopped_vehicles,

        }

    else:

        prev = previous[edge_id]

    previous_speed_kmh = (
        prev["speed"]
    )

    previous_vehicle_count = (
        prev["vehicles"]
    )

    previous_density = (
        prev["density"]
    )

    previous_queue_length_m = (
        prev["queue"]
    )

    previous_stopped_vehicles = (
        prev["stopped"]
    )

    # --------------------------------------------------------
    # FIRST DIFFERENCES
    # --------------------------------------------------------

    speed_change_kmh = (
        average_speed_kmh
        -
        previous_speed_kmh
    )

    vehicle_change = (
        vehicle_count
        -
        previous_vehicle_count
    )

    density_change = (
        density_veh_per_km
        -
        previous_density
    )

    queue_change_m = (
        queue_length_estimate_m
        -
        previous_queue_length_m
    )

    stopped_change = (
        stopped_vehicles
        -
        previous_stopped_vehicles
    )

    # --------------------------------------------------------
    # PERCENT CHANGES
    # --------------------------------------------------------

    speed_change_pct = safe_div(
        speed_change_kmh,
        max(
            abs(previous_speed_kmh),
            1.0
        )
    )

    vehicle_change_pct = safe_div(
        vehicle_change,
        max(
            abs(previous_vehicle_count),
            1.0
        )
    )

    # --------------------------------------------------------
    # STORE CURRENT STATE
    # --------------------------------------------------------

    previous[edge_id] = {

        "speed":
            average_speed_kmh,

        "vehicles":
            vehicle_count,

        "density":
            density_veh_per_km,

        "queue":
            queue_length_estimate_m,

        "stopped":
            stopped_vehicles,

    }

    # --------------------------------------------------------
    # BASE FEATURES
    # --------------------------------------------------------

    features = {

        "vehicle_count":
            vehicle_count,

        "average_speed_kmh":
            average_speed_kmh,

        "stopped_vehicles":
            stopped_vehicles,

        "average_waiting_time":
            average_waiting_time,

        "density_veh_per_km":
            density_veh_per_km,

        "queue_length_estimate_m":
            queue_length_estimate_m,

        "road_length_m":
            road_length_m,

        "vehicles_per_100m":
            vehicles_per_100m,

        "queue_ratio":
            queue_ratio,

        "previous_speed_kmh":
            previous_speed_kmh,

        "previous_vehicle_count":
            previous_vehicle_count,

        "previous_density":
            previous_density,

        "previous_queue_length_m":
            previous_queue_length_m,

        "speed_change_kmh":
            speed_change_kmh,

        "vehicle_change":
            vehicle_change,

        "density_change":
            density_change,

        "queue_change_m":
            queue_change_m,

        "speed_change_pct":
            speed_change_pct,

        "vehicle_change_pct":
            vehicle_change_pct,

    }

    return features


# ============================================================
# START SUMO
# ============================================================

print()
print("=" * 70)
print(" STARTING SUMO")
print("=" * 70)

sumo_cmd = [

    SUMO_BINARY,

    "-c",

    SUMO_CONFIG,

    "--start",

    "--quit-on-end",

]

try:

    traci.start(sumo_cmd)

except Exception as e:

    print()
    print("ERROR: Could not start SUMO.")
    print(e)
    sys.exit(1)


print()
print("TraCI connection established.")


# ============================================================
# GET EDGES
# ============================================================

edges = traci.edge.getIDList()

print()
print("Edges:", len(edges))


# Remove SUMO internal junction edges
edges = [

    e for e in edges

    if not e.startswith(":")

]

print(
    "Usable edges:",
    len(edges)
)


# ============================================================
# SIMULATION LOOP
# ============================================================

step_counter = 0

try:

    while step_counter < MAX_STEPS:

        # ----------------------------------------------------
        # CHECK WHETHER SUMO HAS COMPLETELY FINISHED
        # ----------------------------------------------------

        try:

            expected = (
                traci.simulation
                .getMinExpectedNumber()
            )

        except Exception:

            expected = 0

        # If no vehicles remain, we still perform a few
        # additional steps only if possible.
        #
        # The fixed MAX_STEPS is primarily for live testing.

        if (
            expected <= 0
            and step_counter > 50
        ):

            print()
            print(
                "[TRAFFICX] SUMO has no expected "
                "vehicles remaining."
            )

            print(
                "[TRAFFICX] Ending simulation."
            )

            break

        # ----------------------------------------------------
        # ADVANCE SIMULATION
        # ----------------------------------------------------

        try:

            traci.simulationStep()

        except Exception as e:

            print()
            print(
                "[TRAFFICX] SUMO simulation ended:"
            )

            print(e)

            break

        step_counter += 1

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        if step_counter % 100 == 0:

            print(
                f"[TRAFFICX] "
                f"Simulation progressing: "
                f"step {step_counter}"
            )

        # ----------------------------------------------------
        # COLLECT EDGE FEATURES
        # ----------------------------------------------------

        rows = []

        edge_ids_for_rows = []

        for edge_id in edges:

            try:

                features = (
                    collect_edge_features(
                        edge_id
                    )
                )

                rows.append(features)

                edge_ids_for_rows.append(
                    edge_id
                )

            except Exception:

                continue

        if not rows:

            continue

        # ----------------------------------------------------
        # CREATE DATAFRAME
        # ----------------------------------------------------

        df = pd.DataFrame(rows)

        # Keep road ID
        df["road_id"] = (
            edge_ids_for_rows
        )

        # Keep simulation step
        df["step"] = step_counter

        # ====================================================
        # V15 TEMPORAL FEATURE SCHEMA
        # ====================================================

        temporal_features = [

            "speed_lag2",
            "vehicle_lag2",
            "density_lag2",
            "queue_lag2",
            "stopped_lag2",

            "speed_lag3",
            "vehicle_lag3",
            "density_lag3",
            "queue_lag3",
            "stopped_lag3",

            "speed_change_2step",
            "vehicle_change_2step",
            "density_change_2step",
            "queue_change_2step",
            "stopped_change_2step",

            "speed_change_3step",
            "vehicle_change_3step",
            "density_change_3step",
            "queue_change_3step",
            "stopped_change_3step",

            "speed_reduction_rate",
            "density_growth_rate",
            "queue_growth_rate",
            "vehicle_growth_rate",
            "stopped_growth_rate",

            "speed_acceleration",
            "density_acceleration",
            "queue_acceleration",
            "vehicle_acceleration",
            "stopped_acceleration",

            "traffic_pressure",
            "queue_density_pressure",
            "speed_density_ratio",
            "escalation_score",

        ]

        for col in temporal_features:

            if col not in df.columns:

                df[col] = 0.0

        # ====================================================
        # DERIVED CURRENT FEATURES
        # ====================================================

        df["traffic_pressure"] = (

            df["density_veh_per_km"]

            *

            (
                1.0

                -

                np.clip(

                    df["average_speed_kmh"]
                    / 60.0,

                    0,

                    1

                )
            )
        )

        df["queue_density_pressure"] = (

            df["queue_ratio"]

            *

            df["density_veh_per_km"]

        )

        df["speed_density_ratio"] = (

            df["density_veh_per_km"]

            /

            np.maximum(

                df["average_speed_kmh"],

                1.0

            )

        )

        df["escalation_score"] = (

            df["density_change"]
            .clip(lower=0)

            +

            df["queue_change_m"]
            .clip(lower=0)

            +

            (
                -df["speed_change_kmh"]
            ).clip(lower=0)

        )

        # ====================================================
        # EXACT V15 FEATURE ORDER
        # ====================================================

        feature_columns = [

            "vehicle_count",
            "average_speed_kmh",
            "stopped_vehicles",
            "average_waiting_time",
            "density_veh_per_km",
            "queue_length_estimate_m",
            "road_length_m",
            "vehicles_per_100m",
            "queue_ratio",

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

            "speed_lag2",
            "vehicle_lag2",
            "density_lag2",
            "queue_lag2",
            "stopped_lag2",

            "speed_lag3",
            "vehicle_lag3",
            "density_lag3",
            "queue_lag3",
            "stopped_lag3",

            "speed_change_2step",
            "vehicle_change_2step",
            "density_change_2step",
            "queue_change_2step",
            "stopped_change_2step",

            "speed_change_3step",
            "vehicle_change_3step",
            "density_change_3step",
            "queue_change_3step",
            "stopped_change_3step",

            "speed_reduction_rate",
            "density_growth_rate",
            "queue_growth_rate",
            "vehicle_growth_rate",
            "stopped_growth_rate",

            "speed_acceleration",
            "density_acceleration",
            "queue_acceleration",
            "vehicle_acceleration",
            "stopped_acceleration",

            "traffic_pressure",
            "queue_density_pressure",
            "speed_density_ratio",
            "escalation_score",

        ]

        X = df[feature_columns]

        # ====================================================
        # PREDICTION
        # ====================================================

        try:

            probabilities = (
                model.predict_proba(X)[:, 1]
            )

        except Exception as e:

            print()
            print(
                "[TRAFFICX] Prediction error:"
            )

            print(e)

            continue

        df["risk_probability"] = (
            probabilities
        )

        df["predicted_risk"] = (

            probabilities >= THRESHOLD

        ).astype(int)

        # ====================================================
        # SUMMARY
        # ====================================================

        max_probability = (
            probabilities.max()
        )

        mean_probability = (
            probabilities.mean()
        )

        risk_count = int(
            df["predicted_risk"].sum()
        )

        # ====================================================
        # STORE LIVE OUTPUT
        # ====================================================

        output_columns = [

            "step",
            "road_id",

            "vehicle_count",
            "average_speed_kmh",
            "stopped_vehicles",

            "average_waiting_time",

            "density_veh_per_km",

            "queue_length_estimate_m",

            "risk_probability",

            "predicted_risk",

        ]

        live_output = (
            df[output_columns]
            .copy()
        )

        live_output["scenario"] = (
            SCENARIO
        )

        all_predictions.append(
            live_output
        )

        # ====================================================
        # PRINT RESULTS
        # ====================================================

        if step_counter % PRINT_INTERVAL == 0:

            print()
            print("=" * 70)

            print(
                f"SIMULATION STEP : "
                f"{step_counter}"
            )

            print("=" * 70)

            print(
                f"Edges analyzed       : "
                f"{len(df)}"
            )

            print(
                f"Mean risk probability: "
                f"{mean_probability:.4f}"
            )

            print(
                f"Maximum risk         : "
                f"{max_probability:.4f}"
            )

            print(
                f"High-risk edges      : "
                f"{risk_count}"
            )

            # ------------------------------------------------
            # TOP RISK EDGES
            # ------------------------------------------------

            top = df.nlargest(
                5,
                "risk_probability"
            )

            print()
            print("TOP RISK EDGES")

            print(
                "-" * 70
            )

            for _, row in top.iterrows():

                risk = (
                    row["risk_probability"]
                )

                if risk >= THRESHOLD:

                    status = "HIGH RISK"

                elif risk >= 0.70:

                    status = "WARNING"

                else:

                    status = "LOW"

                print(

                    f"{str(row['road_id']):25s} | "

                    f"risk={risk:.4f} | "

                    f"{status:10s} | "

                    f"vehicles="
                    f"{int(row['vehicle_count']):3d} | "

                    f"speed="
                    f"{row['average_speed_kmh']:6.1f} | "

                    f"density="
                    f"{row['density_veh_per_km']:7.2f} | "

                    f"queue="
                    f"{row['queue_length_estimate_m']:7.1f}"

                )


finally:

    print()
    print("=" * 70)
    print("CLOSING TRAFFICX")
    print("=" * 70)

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    if all_predictions:

        try:

            final_output = pd.concat(
                all_predictions,
                ignore_index=True
            )

            # Put scenario first
            final_output = final_output[

                [
                    "scenario",
                    "step",
                    "road_id",

                    "vehicle_count",
                    "average_speed_kmh",
                    "stopped_vehicles",
                    "average_waiting_time",

                    "density_veh_per_km",
                    "queue_length_estimate_m",

                    "risk_probability",
                    "predicted_risk",

                ]

            ]

            final_output.to_csv(
                OUTPUT_FILE,
                index=False
            )

            print()
            print(
                "Live predictions saved:"
            )

            print(
                OUTPUT_FILE
            )

            print(
                "Prediction rows:",
                len(final_output)
            )

        except Exception as e:

            print()
            print(
                "WARNING: Could not save "
                "live predictions."
            )

            print(e)

    # ========================================================
    # CLOSE TRACI
    # ========================================================

    try:

        traci.close()

    except Exception:

        pass

    print(
        "TraCI closed."
    )

    print()
    print(
        f"TRAFFICX finished at "
        f"simulation step {step_counter}."
    )

    print("=" * 70)