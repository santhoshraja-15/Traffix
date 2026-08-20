import os
import sys
import pandas as pd
import networkx as nx

# ============================================================
# TRAFFICX V15 - RISK AWARE ROUTER
# ============================================================

BASE_DIR = r"D:\TRAFFICX"
SCENARIO = "medium"

PREDICTION_FILE = (
    rf"{BASE_DIR}\models\trafficx_v15_live_predictions_{SCENARIO}.csv"
)

NETWORK_FILE = (
    rf"{BASE_DIR}\scenarios\{SCENARIO}\osm.net.xml.gz"
)

OUTPUT_FILE = (
    rf"{BASE_DIR}\models\trafficx_v15_route_comparison_{SCENARIO}.csv"
)

# Controls how strongly predicted risk affects routing.
RISK_WEIGHT = 500.0

print("=" * 70)
print(" TRAFFICX - V15 RISK AWARE ROUTER")
print("=" * 70)

print()
print("Scenario:", SCENARIO)
print("Prediction file:")
print(PREDICTION_FILE)

print()
print("Network:")
print(NETWORK_FILE)


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(PREDICTION_FILE):
    raise FileNotFoundError(PREDICTION_FILE)

if not os.path.exists(NETWORK_FILE):
    raise FileNotFoundError(NETWORK_FILE)


# ============================================================
# LOAD SUMO
# ============================================================

SUMO_HOME = os.environ.get("SUMO_HOME")

if not SUMO_HOME:
    raise RuntimeError("SUMO_HOME environment variable is not set.")

sys.path.append(
    os.path.join(SUMO_HOME, "tools")
)

import sumolib


# ============================================================
# LOAD NETWORK
# ============================================================

print()
print("=" * 70)
print(" LOADING NETWORK")
print("=" * 70)

net = sumolib.net.readNet(NETWORK_FILE)

sumo_edges = list(net.getEdges())

print()
print("SUMO edges:", len(sumo_edges))


# ============================================================
# BUILD NETWORKX GRAPH
# ============================================================

G = nx.DiGraph()

edge_info = {}


for edge in sumo_edges:

    edge_id = edge.getID()

    # Ignore SUMO internal junction edges.
    if edge_id.startswith(":"):
        continue

    from_node = edge.getFromNode().getID()
    to_node = edge.getToNode().getID()

    length = float(edge.getLength())

    if length <= 0:
        continue

    try:
        speed = float(edge.getSpeed())
    except Exception:
        speed = 0.0

    G.add_edge(
        from_node,
        to_node,
        edge_id=edge_id,
        length=length,
        speed=speed,
    )

    edge_info[edge_id] = {
        "from": from_node,
        "to": to_node,
        "length": length,
        "speed": speed,
    }


print()
print("Network nodes:", G.number_of_nodes())
print("Network edges:", G.number_of_edges())


# ============================================================
# LOAD V15 PREDICTIONS
# ============================================================

print()
print("=" * 70)
print(" LOADING V15 PREDICTIONS")
print("=" * 70)

pred = pd.read_csv(
    PREDICTION_FILE,
    low_memory=False,
)

print()
print("Prediction rows:", len(pred))


# ============================================================
# FIND REQUIRED COLUMNS
# ============================================================

edge_candidates = [
    "edge_id",
    "road_id",
    "edge",
    "road",
]

edge_column = None

for column in edge_candidates:
    if column in pred.columns:
        edge_column = column
        break


if edge_column is None:
    raise RuntimeError(
        "No edge identifier found in prediction file. "
        "Expected edge_id or road_id."
    )


step_candidates = [
    "step",
    "simulation_step",
    "time",
]

step_column = None

for column in step_candidates:
    if column in pred.columns:
        step_column = column
        break


if step_column is None:
    raise RuntimeError(
        "No simulation step column found."
    )


risk_candidates = [
    "risk_probability",
    "predicted_probability",
    "risk_prob",
]

risk_column = None

for column in risk_candidates:
    if column in pred.columns:
        risk_column = column
        break


if risk_column is None:
    raise RuntimeError(
        "No risk probability column found."
    )


print()
print("Edge column :", edge_column)
print("Step column :", step_column)
print("Risk column :", risk_column)


# ============================================================
# GET LATEST STEP
# ============================================================

latest_step = pred[step_column].max()

print()
print("Latest simulation step:", latest_step)


current = pred[
    pred[step_column] == latest_step
].copy()


print(
    "Current prediction rows:",
    len(current)
)


# ============================================================
# NORMALIZE DATA
# ============================================================

current[edge_column] = (
    current[edge_column]
    .astype(str)
    .str.strip()
)

current[risk_column] = pd.to_numeric(
    current[risk_column],
    errors="coerce"
).fillna(0.0)


# One prediction per road.
current = (
    current
    .sort_values(
        risk_column,
        ascending=False
    )
    .drop_duplicates(
        subset=[edge_column]
    )
)


# ============================================================
# CREATE RISK LOOKUP
# ============================================================

risk_lookup = dict(
    zip(
        current[edge_column],
        current[risk_column]
    )
)


# ============================================================
# MATCH NETWORK
# ============================================================

matched = 0

for edge_id in edge_info:

    if edge_id in risk_lookup:
        matched += 1


print()
print(
    "Network edges matched with predictions:",
    matched
)


if matched == 0:
    raise RuntimeError(
        "No SUMO network edges matched the V15 predictions."
    )


# ============================================================
# FIND VALID CONNECTED SOURCE / DESTINATION
# ============================================================

print()
print("=" * 70)
print(" FINDING VALID ROUTE")
print("=" * 70)


# Strongly connected components guarantee that a directed
# path exists between the selected nodes.

components = list(
    nx.strongly_connected_components(G)
)

components.sort(
    key=len,
    reverse=True
)


if len(components) == 0:
    raise RuntimeError(
        "No connected components found."
    )


largest = components[0]

print()
print(
    "Largest strongly connected component:",
    len(largest),
    "nodes"
)


if len(largest) < 2:
    raise RuntimeError(
        "Largest component contains fewer than 2 nodes."
    )


nodes = list(largest)


# ============================================================
# SELECT A REASONABLY LONG VALID ROUTE
# ============================================================

source = None
destination = None
best_distance = 0.0

# Test a limited number of nodes.
sample = nodes[
    :min(100, len(nodes))
]


for candidate_source in sample:

    try:

        distances = nx.single_source_dijkstra_path_length(
            G,
            candidate_source,
            weight="length"
        )

    except Exception:
        continue

    for candidate_destination, distance in distances.items():

        if candidate_destination == candidate_source:
            continue

        if distance > best_distance:

            best_distance = distance
            source = candidate_source
            destination = candidate_destination


if source is None or destination is None:

    raise RuntimeError(
        "Could not find a valid source/destination pair."
    )


print()
print("Source:", source)
print("Destination:", destination)

print(
    "Baseline distance:",
    round(best_distance / 1000.0, 3),
    "km"
)


# ============================================================
# ROUTING WEIGHTS
# ============================================================

def shortest_weight(u, v, data):

    return data["length"]


def risk_aware_weight(u, v, data):

    edge_id = data["edge_id"]

    length = data["length"]

    risk = risk_lookup.get(
        edge_id,
        0.0
    )

    return (
        length +
        (risk * RISK_WEIGHT)
    )


# ============================================================
# CALCULATE SHORTEST ROUTE
# ============================================================

print()
print("=" * 70)
print(" CALCULATING SHORTEST ROUTE")
print("=" * 70)

shortest_nodes = nx.shortest_path(
    G,
    source,
    destination,
    weight=shortest_weight,
)


# ============================================================
# CALCULATE RISK AWARE ROUTE
# ============================================================

print()
print("=" * 70)
print(" CALCULATING V15 RISK-AWARE ROUTE")
print("=" * 70)

risk_nodes = nx.shortest_path(
    G,
    source,
    destination,
    weight=risk_aware_weight,
)


# ============================================================
# NODE PATH -> EDGE PATH
# ============================================================

def nodes_to_edges(path):

    result = []

    for i in range(len(path) - 1):

        u = path[i]
        v = path[i + 1]

        result.append(
            G[u][v]["edge_id"]
        )

    return result


shortest_edges = nodes_to_edges(
    shortest_nodes
)

risk_edges = nodes_to_edges(
    risk_nodes
)


# ============================================================
# ROUTE STATISTICS
# ============================================================

def calculate_statistics(edges):

    distance = 0.0
    risk_exposure = 0.0

    risk_values = []

    high_risk_count = 0

    matched_count = 0

    for edge_id in edges:

        if edge_id not in edge_info:
            continue

        length = edge_info[edge_id]["length"]

        risk = risk_lookup.get(
            edge_id,
            0.0
        )

        distance += length

        risk_values.append(
            risk
        )

        risk_exposure += (
            risk * length
        )

        if edge_id in risk_lookup:
            matched_count += 1

        if risk >= 0.50:
            high_risk_count += 1


    if len(risk_values) > 0:

        average_risk = (
            sum(risk_values) /
            len(risk_values)
        )

        maximum_risk = max(
            risk_values
        )

    else:

        average_risk = 0.0
        maximum_risk = 0.0


    return {
        "distance_m": distance,
        "distance_km": distance / 1000.0,
        "edge_count": len(edges),
        "average_risk": average_risk,
        "maximum_risk": maximum_risk,
        "risk_exposure": risk_exposure,
        "high_risk_edges": high_risk_count,
        "matched_edges": matched_count,
    }


shortest_stats = calculate_statistics(
    shortest_edges
)

risk_stats = calculate_statistics(
    risk_edges
)


# ============================================================
# PRINT RESULTS
# ============================================================

print()
print("=" * 70)
print(" ROUTE COMPARISON")
print("=" * 70)


print()
print("NORMAL SHORTEST ROUTE")
print("-" * 70)

print(
    f"Distance        : "
    f"{shortest_stats['distance_km']:.3f} km"
)

print(
    f"Edges           : "
    f"{shortest_stats['edge_count']}"
)

print(
    f"Average risk    : "
    f"{shortest_stats['average_risk']:.4f}"
)

print(
    f"Maximum risk    : "
    f"{shortest_stats['maximum_risk']:.4f}"
)

print(
    f"Risk exposure   : "
    f"{shortest_stats['risk_exposure']:.2f}"
)

print(
    f"High-risk edges : "
    f"{shortest_stats['high_risk_edges']}"
)


print()
print("V15 RISK-AWARE ROUTE")
print("-" * 70)

print(
    f"Distance        : "
    f"{risk_stats['distance_km']:.3f} km"
)

print(
    f"Edges           : "
    f"{risk_stats['edge_count']}"
)

print(
    f"Average risk    : "
    f"{risk_stats['average_risk']:.4f}"
)

print(
    f"Maximum risk    : "
    f"{risk_stats['maximum_risk']:.4f}"
)

print(
    f"Risk exposure   : "
    f"{risk_stats['risk_exposure']:.2f}"
)

print(
    f"High-risk edges : "
    f"{risk_stats['high_risk_edges']}"
)


# ============================================================
# IMPROVEMENT
# ============================================================

distance_difference = (
    risk_stats["distance_km"]
    -
    shortest_stats["distance_km"]
)


if shortest_stats["risk_exposure"] > 0:

    risk_reduction = (
        (
            shortest_stats["risk_exposure"]
            -
            risk_stats["risk_exposure"]
        )
        /
        shortest_stats["risk_exposure"]
    ) * 100.0

else:

    risk_reduction = 0.0


if shortest_stats["average_risk"] > 0:

    average_risk_reduction = (
        (
            shortest_stats["average_risk"]
            -
            risk_stats["average_risk"]
        )
        /
        shortest_stats["average_risk"]
    ) * 100.0

else:

    average_risk_reduction = 0.0


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 70)
print(" TRAFFICX OPTIMIZATION RESULT")
print("=" * 70)

print()

print(
    f"Extra distance          : "
    f"{distance_difference:+.3f} km"
)

print(
    f"Average-risk reduction  : "
    f"{average_risk_reduction:.2f}%"
)

print(
    f"Risk-exposure reduction : "
    f"{risk_reduction:.2f}%"
)


if risk_reduction > 0:

    print()
    print(
        "TRAFFICX found a lower-risk route."
    )

else:

    print()
    print(
        "Shortest route is currently competitive."
    )


# ============================================================
# SAVE RESULT
# ============================================================

results = pd.DataFrame(
    [
        {
            "scenario": SCENARIO,
            "simulation_step": latest_step,
            "source": source,
            "destination": destination,
            "route_type": "SHORTEST",
            "distance_km": shortest_stats["distance_km"],
            "edge_count": shortest_stats["edge_count"],
            "average_risk": shortest_stats["average_risk"],
            "maximum_risk": shortest_stats["maximum_risk"],
            "risk_exposure": shortest_stats["risk_exposure"],
            "high_risk_edges": shortest_stats["high_risk_edges"],
            "route_edges": "|".join(shortest_edges),
        },
        {
            "scenario": SCENARIO,
            "simulation_step": latest_step,
            "source": source,
            "destination": destination,
            "route_type": "V15_RISK_AWARE",
            "distance_km": risk_stats["distance_km"],
            "edge_count": risk_stats["edge_count"],
            "average_risk": risk_stats["average_risk"],
            "maximum_risk": risk_stats["maximum_risk"],
            "risk_exposure": risk_stats["risk_exposure"],
            "high_risk_edges": risk_stats["high_risk_edges"],
            "route_edges": "|".join(risk_edges),
        },
    ]
)


results.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# PRINT ROUTES
# ============================================================

print()
print("=" * 70)
print(" SHORTEST ROUTE")
print("=" * 70)

for i, edge_id in enumerate(
    shortest_edges,
    start=1
):

    risk = risk_lookup.get(
        edge_id,
        0.0
    )

    print(
        f"{i:4d}. "
        f"{edge_id:30s} "
        f"risk={risk:.4f}"
    )


print()
print("=" * 70)
print(" V15 RISK-AWARE ROUTE")
print("=" * 70)

for i, edge_id in enumerate(
    risk_edges,
    start=1
):

    risk = risk_lookup.get(
        edge_id,
        0.0
    )

    print(
        f"{i:4d}. "
        f"{edge_id:30s} "
        f"risk={risk:.4f}"
    )


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 70)
print(" ROUTING COMPLETE")
print("=" * 70)

print()
print("Saved:")
print(OUTPUT_FILE)

print()
print(
    "SUMO -> V15 prediction -> "
    "risk-aware routing"
)

print("=" * 70)