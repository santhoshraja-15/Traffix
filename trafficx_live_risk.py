import os
import sys
import json
import math
import time

import numpy as np
import pandas as pd
import xgboost as xgb
import traci


# ============================================================
# TRAFFICX - LIVE RISK ENGINE
# V10 INFERENCE
# ============================================================

BASE_DIR = r"D:\TRAFFICX"

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trafficx_xgboost_v10.json"
)

FEATURE_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trafficx_xgboost_v10_features.json"
)

# ------------------------------------------------------------
# SUMO
# ------------------------------------------------------------

SUMO_BINARY = "sumo-gui"

SUMO_CONFIG = r"D:\TRAFFICX\sumo\trafficx.sumocfg"


# ============================================================
# V10 FEATURES
# ============================================================

FEATURES = [
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


# ============================================================
# MODEL
# ============================================================

print()
print("=" * 70)
print(" TRAFFICX - LIVE RISK ENGINE")
print("=" * 70)

print()
print("Loading V10 model...")

model = xgb.XGBClassifier()

model.load_model(
    MODEL_PATH
)

print("V10 model loaded successfully.")

print()
print("Feature count:", len(FEATURES))

# ============================================================
# FEATURE HISTORY
# ============================================================

history = {}

MAX_HISTORY = 60


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_mean(values):

    if not values:
        return 0.0

    return float(
        np.mean(values)
    )


def safe_diff(history_values, steps_back):

    if len(history_values) <= steps_back:
        return 0.0

    return float(
        history_values[-1]
        - history_values[-1 - steps_back]
    )


def safe_mean_window(
    history_values,
    window
):

    if not history_values:
        return 0.0

    values = history_values[
        -window:
    ]

    return float(
        np.mean(values)
    )


# ============================================================
# EDGE STATE
# ============================================================

def get_edge_state(edge_id):

    try:

        vehicle_ids = traci.edge.getLastStepVehicleIDs(
            edge_id
        )

        vehicle_count = len(
            vehicle_ids
        )

        mean_speed_ms = traci.edge.getLastStepMeanSpeed(
            edge_id
        )

        if mean_speed_ms < 0:
            mean_speed_ms = 0.0

        average_speed_kmh = (
            mean_speed_ms * 3.6
        )

        halted = traci.edge.getLastStepHaltingNumber(
            edge_id
        )

        mean_waiting = traci.edge.getWaitingTime(
            edge_id
        )

        if mean_waiting < 0:
            mean_waiting = 0.0

        length = traci.edge.getLastStepLength(
            edge_id
        )

        # SUMO edge length
        if length <= 0:

            length = traci.lane.getLength(
                traci.edge.getLaneNumber(edge_id)
            )

        # Basic density
        if length > 0:

            density = (
                vehicle_count
                / (length / 1000.0)
            )

        else:

            density = 0.0

        # Simple queue estimate
        queue_length = (
            halted * 7.0
        )

        return {

            "road_length_m":
                float(length),

            "vehicle_count":
                float(vehicle_count),

            "average_speed_kmh":
                float(average_speed_kmh),

            "stopped_vehicles":
                float(halted),

            "average_waiting_time":
                float(mean_waiting),

            "density_veh_per_km":
                float(density),

            "queue_length_estimate_m":
                float(queue_length)
        }

    except Exception as e:

        print(
            f"Warning reading edge {edge_id}: {e}"
        )

        return None


# ============================================================
# UPDATE HISTORY
# ============================================================

def update_history(
    edge_id,
    state
):

    if edge_id not in history:

        history[edge_id] = {

            "speed": [],
            "vehicle": [],
            "stopped": [],
            "waiting": [],
            "density": [],
            "queue": []
        }

    h = history[edge_id]

    h["speed"].append(
        state["average_speed_kmh"]
    )

    h["vehicle"].append(
        state["vehicle_count"]
    )

    h["stopped"].append(
        state["stopped_vehicles"]
    )

    h["waiting"].append(
        state["average_waiting_time"]
    )

    h["density"].append(
        state["density_veh_per_km"]
    )

    h["queue"].append(
        state["queue_length_estimate_m"]
    )

    for key in h:

        if len(h[key]) > MAX_HISTORY:

            h[key] = h[key][-MAX_HISTORY:]


# ============================================================
# BUILD V10 FEATURES
# ============================================================

def build_features(
    edge_id,
    state
):

    h = history[edge_id]

    speed = h["speed"]
    vehicle = h["vehicle"]
    stopped = h["stopped"]
    waiting = h["waiting"]
    density = h["density"]
    queue = h["queue"]

    features = {}

    # --------------------------------------------------------
    # BASE
    # --------------------------------------------------------

    features[
        "road_length_m"
    ] = state["road_length_m"]

    features[
        "vehicle_count"
    ] = state["vehicle_count"]

    features[
        "average_speed_kmh"
    ] = state["average_speed_kmh"]

    features[
        "stopped_vehicles"
    ] = state["stopped_vehicles"]

    features[
        "average_waiting_time"
    ] = state["average_waiting_time"]

    features[
        "density_veh_per_km"
    ] = state["density_veh_per_km"]

    features[
        "queue_length_estimate_m"
    ] = state["queue_length_estimate_m"]

    # We need the exact encoding used by training.
    # Do NOT assume this is correct until we inspect the dataset.
    features[
        "current_congestion_encoded"
    ] = 0.0

    features[
        "scenario_encoded"
    ] = 0.0

    # --------------------------------------------------------
    # CHANGES
    # --------------------------------------------------------

    features[
        "speed_change"
    ] = safe_diff(speed, 1)

    features[
        "vehicle_change"
    ] = safe_diff(vehicle, 1)

    features[
        "stopped_change"
    ] = safe_diff(stopped, 1)

    features[
        "waiting_change"
    ] = safe_diff(waiting, 1)

    features[
        "density_change"
    ] = safe_diff(density, 1)

    features[
        "queue_change"
    ] = safe_diff(queue, 1)

    # --------------------------------------------------------
    # WINDOWED CHANGES
    # --------------------------------------------------------

    for window in [
        5,
        15,
        30,
        60
    ]:

        features[
            f"speed_change_{window}s"
        ] = safe_diff(
            speed,
            window
        )

        features[
            f"density_change_{window}s"
        ] = safe_diff(
            density,
            window
        )

        features[
            f"queue_change_{window}s"
        ] = safe_diff(
            queue,
            window
        )

        features[
            f"waiting_change_{window}s"
        ] = safe_diff(
            waiting,
            window
        )

    # --------------------------------------------------------
    # WINDOWED MEANS
    # --------------------------------------------------------

    for window in [
        15,
        30,
        60
    ]:

        features[
            f"speed_mean_{window}s"
        ] = safe_mean_window(
            speed,
            window
        )

        features[
            f"density_mean_{window}s"
        ] = safe_mean_window(
            density,
            window
        )

        features[
            f"queue_mean_{window}s"
        ] = safe_mean_window(
            queue,
            window
        )

        features[
            f"waiting_mean_{window}s"
        ] = safe_mean_window(
            waiting,
            window
        )

    # --------------------------------------------------------
    # ACCELERATION
    # --------------------------------------------------------

    if len(speed) >= 3:

        features[
            "speed_acceleration"
        ] = (
            speed[-1]
            - 2 * speed[-2]
            + speed[-3]
        )

    else:

        features[
            "speed_acceleration"
        ] = 0.0

    if len(density) >= 3:

        features[
            "density_acceleration"
        ] = (
            density[-1]
            - 2 * density[-2]
            + density[-3]
        )

    else:

        features[
            "density_acceleration"
        ] = 0.0

    if len(queue) >= 3:

        features[
            "queue_acceleration"
        ] = (
            queue[-1]
            - 2 * queue[-2]
            + queue[-3]
        )

    else:

        features[
            "queue_acceleration"
        ] = 0.0

    return features


# ============================================================
# PREDICTION
# ============================================================

def predict_risk(
    feature_dict
):

    row = pd.DataFrame(
        [[
            feature_dict[f]
            for f in FEATURES
        ]],
        columns=FEATURES
    )

    probability = float(
        model.predict_proba(row)[0, 1]
    )

    risk = (
        probability >= 0.635
    )

    return probability, risk


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
    SUMO_CONFIG
]

traci.start(
    sumo_cmd
)

print()
print("TraCI connected.")

# ============================================================
# EDGE LIST
# ============================================================

edge_ids = traci.edge.getIDList()

# Remove internal SUMO edges
edge_ids = [
    e
    for e in edge_ids
    if not e.startswith(":")
]

print(
    "Edges monitored:",
    len(edge_ids)
)

# ============================================================
# MAIN LOOP
# ============================================================

STEP = 0

try:

    while STEP < 1000:

        traci.simulationStep()

        STEP += 1

        risk_results = []

        for edge_id in edge_ids:

            state = get_edge_state(
                edge_id
            )

            if state is None:
                continue

            update_history(
                edge_id,
                state
            )

            features = build_features(
                edge_id,
                state
            )

            probability, risk = predict_risk(
                features
            )

            risk_results.append({

                "edge": edge_id,

                "vehicles":
                    state["vehicle_count"],

                "speed":
                    state["average_speed_kmh"],

                "density":
                    state["density_veh_per_km"],

                "queue":
                    state["queue_length_estimate_m"],

                "waiting":
                    state["average_waiting_time"],

                "risk_probability":
                    probability,

                "risk":
                    risk
            })

        # ----------------------------------------------------
        # PRINT TOP RISK EDGES
        # ----------------------------------------------------

        if STEP % 10 == 0:

            risk_results.sort(
                key=lambda x:
                    x["risk_probability"],
                reverse=True
            )

            print()
            print(
                "=" * 70
            )

            print(
                f"SIMULATION STEP: {STEP}"
            )

            print(
                "=" * 70
            )

            for result in risk_results[:10]:

                status = (
                    "RISK"
                    if result["risk"]
                    else "NON-RISK"
                )

                print(
                    f"{result['edge']:20s} "
                    f"vehicles={result['vehicles']:5.0f} "
                    f"speed={result['speed']:6.1f} "
                    f"density={result['density']:7.1f} "
                    f"queue={result['queue']:7.1f} "
                    f"risk={result['risk_probability']:.3f} "
                    f"{status}"
                )


except KeyboardInterrupt:

    print()
    print(
        "Simulation interrupted."
    )

finally:

    traci.close()

    print()
    print(
        "TraCI connection closed."
    )

print()
print("=" * 70)
print(" TRAFFICX LIVE RISK ENGINE STOPPED")
print("=" * 70)