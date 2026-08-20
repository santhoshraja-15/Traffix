import os
import sys
import csv
import traci

# ============================================================
# TRAFFICX - MULTI-SCENARIO ROAD-LEVEL DATA COLLECTOR
# ============================================================

if "SUMO_HOME" not in os.environ:
    sys.exit("SUMO_HOME environment variable is not set.")


SUMO_BINARY = os.path.join(
    os.environ["SUMO_HOME"],
    "bin",
    "sumo.exe"
)

BASE_DIR = r"D:\TRAFFICX\scenarios"
OUTPUT_DIR = r"D:\TRAFFICX\road_datasets"

SCENARIOS = [
    "low",
    "medium",
    "high",
    "congested"
]

TOTAL_STEPS = 1000

STOP_SPEED = 5 / 3.6

AVERAGE_VEHICLE_LENGTH = 5.0


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# RUN ONE SCENARIO
# ============================================================

def run_scenario(scenario):

    print("\n")
    print("========================================")
    print(f" TRAFFICX - {scenario.upper()} ROAD DATA")
    print("========================================")

    scenario_dir = os.path.join(
        BASE_DIR,
        scenario
    )

    sumo_config = os.path.join(
        scenario_dir,
        "traffic.sumocfg"
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        f"road_{scenario}.csv"
    )

    print(f"Config : {sumo_config}")
    print(f"Output : {output_file}")

    # --------------------------------------------------------
    # Start SUMO
    # --------------------------------------------------------

    print("\nStarting SUMO...")

    traci.start([
        SUMO_BINARY,
        "-c",
        sumo_config,
        "--no-step-log",
        "true"
    ])

    print("Connected to SUMO successfully!")

    # --------------------------------------------------------
    # Discover roads
    # --------------------------------------------------------

    all_edges = traci.edge.getIDList()

    road_edges = [
        edge_id
        for edge_id in all_edges
        if not edge_id.startswith(":")
    ]

    print(
        f"Total edges     : {len(all_edges)}"
    )

    print(
        f"Usable road edges: {len(road_edges)}"
    )

    # --------------------------------------------------------
    # Road lengths
    # --------------------------------------------------------

    road_lengths = {}

    for road_id in road_edges:

        try:

            lane_count = traci.edge.getLaneNumber(
                road_id
            )

            if lane_count > 0:

                lane_id = f"{road_id}_0"

                road_lengths[road_id] = (
                    traci.lane.getLength(
                        lane_id
                    )
                )

            else:

                road_lengths[road_id] = 0.0

        except Exception:

            road_lengths[road_id] = 0.0

    # --------------------------------------------------------
    # Create CSV
    # --------------------------------------------------------

    with open(
        output_file,
        "w",
        newline=""
    ) as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "scenario",
            "step",
            "road_id",
            "road_length_m",
            "vehicle_count",
            "average_speed_kmh",
            "stopped_vehicles",
            "average_waiting_time",
            "density_veh_per_km",
            "queue_length_estimate_m"
        ])

        # ====================================================
        # SIMULATION
        # ====================================================

        for step in range(TOTAL_STEPS):

            traci.simulationStep()

            # ------------------------------------------------
            # Initialize every road
            # ------------------------------------------------

            roads = {}

            for road_id in road_edges:

                roads[road_id] = {
                    "vehicle_count": 0,
                    "total_speed": 0.0,
                    "total_waiting": 0.0,
                    "stopped_vehicles": 0
                }

            # ------------------------------------------------
            # Collect vehicle information
            # ------------------------------------------------

            vehicle_ids = traci.vehicle.getIDList()

            for vehicle_id in vehicle_ids:

                road_id = traci.vehicle.getRoadID(
                    vehicle_id
                )

                # Ignore junction internals
                if road_id.startswith(":"):
                    continue

                if road_id not in roads:
                    continue

                speed = traci.vehicle.getSpeed(
                    vehicle_id
                )

                waiting_time = traci.vehicle.getWaitingTime(
                    vehicle_id
                )

                roads[road_id]["vehicle_count"] += 1

                roads[road_id]["total_speed"] += speed

                roads[road_id]["total_waiting"] += (
                    waiting_time
                )

                if speed < STOP_SPEED:

                    roads[road_id]["stopped_vehicles"] += 1

            # ------------------------------------------------
            # Write ALL roads
            # ------------------------------------------------

            for road_id in road_edges:

                data = roads[road_id]

                vehicle_count = data["vehicle_count"]

                road_length = road_lengths.get(
                    road_id,
                    0.0
                )

                # --------------------------------------------
                # Average speed
                # --------------------------------------------

                if vehicle_count > 0:

                    average_speed_kmh = (
                        data["total_speed"]
                        / vehicle_count
                    ) * 3.6

                    average_waiting_time = (
                        data["total_waiting"]
                        / vehicle_count
                    )

                else:

                    average_speed_kmh = 0.0

                    average_waiting_time = 0.0

                # --------------------------------------------
                # Density
                # --------------------------------------------

                if road_length > 0:

                    density = (
                        vehicle_count
                        / (road_length / 1000)
                    )

                else:

                    density = 0.0

                # --------------------------------------------
                # Queue length estimate
                # --------------------------------------------

                queue_length = (
                    data["stopped_vehicles"]
                    * AVERAGE_VEHICLE_LENGTH
                )

                # --------------------------------------------
                # Write
                # --------------------------------------------

                writer.writerow([
                    scenario,
                    step,
                    road_id,
                    round(road_length, 2),
                    vehicle_count,
                    round(
                        average_speed_kmh,
                        2
                    ),
                    data["stopped_vehicles"],
                    round(
                        average_waiting_time,
                        2
                    ),
                    round(
                        density,
                        2
                    ),
                    round(
                        queue_length,
                        2
                    )
                ])

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            if step % 100 == 0:

                active_roads = sum(
                    1
                    for road_id in road_edges
                    if roads[road_id]["vehicle_count"] > 0
                )

                print(
                    f"Step: {step:4d} | "
                    f"Vehicles: {len(vehicle_ids):4d} | "
                    f"Active roads: {active_roads:4d}"
                )

    # --------------------------------------------------------
    # Close SUMO
    # --------------------------------------------------------

    traci.close()

    print(
        f"\n{scenario.upper()} scenario finished!"
    )

    print(
        f"Dataset saved to:\n"
        f"{output_file}"
    )


# ============================================================
# MAIN
# ============================================================

print("""
========================================
 TRAFFICX
 ROAD-LEVEL MULTI-SCENARIO EXPERIMENT
========================================
""")

for scenario in SCENARIOS:

    run_scenario(
        scenario
    )


print("""
========================================
 ALL ROAD SCENARIOS COMPLETE
========================================
""")

print(
    "Generated inside:"
)

print(
    OUTPUT_DIR
)

print("""
road_low.csv
road_medium.csv
road_high.csv
road_congested.csv
""")