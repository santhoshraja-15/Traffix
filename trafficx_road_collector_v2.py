import os
import sys
import csv
import traci

# ============================================================
# TRAFFICX - Road-Level Traffic Data Collector V2
# ============================================================
#
# Improvements over V1:
#   1. Tracks ALL usable road edges
#   2. Includes roads with zero vehicles
#   3. Aggregates vehicles by road
#   4. Collects road length
#   5. Calculates density
#   6. Calculates queue length estimate
#   7. Keeps scenario information
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

if "SUMO_HOME" not in os.environ:
    sys.exit("SUMO_HOME environment variable is not set.")

sumo_binary = os.path.join(
    os.environ["SUMO_HOME"],
    "bin",
    "sumo-gui.exe"
)

sumo_config = r"D:\TRAFFICX\2026-08-19-23-26-46\osm.sumocfg"

output_file = r"D:\TRAFFICX\road_level_v2.csv"

# Change this when generating LOW/MEDIUM/HIGH/CONGESTED data
SCENARIO = "NORMAL"

TOTAL_STEPS = 1000

# Vehicle considered stopped below 5 km/h
STOP_SPEED = 5 / 3.6

# Approximate vehicle length for queue estimation
AVERAGE_VEHICLE_LENGTH = 5.0


# ============================================================
# START SUMO
# ============================================================

print("\n========================================")
print(" TRAFFICX - ROAD LEVEL COLLECTOR V2")
print("========================================")
print(f"Scenario : {SCENARIO}")
print(f"Steps    : {TOTAL_STEPS}")
print(f"Output   : {output_file}")
print("")

traci.start([
    sumo_binary,
    "-c",
    sumo_config
])

print("Connected to SUMO successfully!")


# ============================================================
# DISCOVER ROAD EDGES
# ============================================================

all_edges = traci.edge.getIDList()

# Remove SUMO internal junction edges.
road_edges = [
    edge_id
    for edge_id in all_edges
    if not edge_id.startswith(":")
]

print(f"Total SUMO edges : {len(all_edges)}")
print(f"Usable road edges: {len(road_edges)}")


# ============================================================
# GET ROAD LENGTHS
# ============================================================

road_lengths = {}

for road_id in road_edges:

    try:
        lane_ids = traci.edge.getLaneNumber(road_id)

        if lane_ids > 0:

            lane_id = f"{road_id}_0"

            length = traci.lane.getLength(lane_id)

            road_lengths[road_id] = length

        else:

            road_lengths[road_id] = 0.0

    except Exception:

        road_lengths[road_id] = 0.0


# ============================================================
# CREATE CSV
# ============================================================

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


    # ========================================================
    # SIMULATION LOOP
    # ========================================================

    for step in range(TOTAL_STEPS):

        traci.simulationStep()


        # ====================================================
        # Initialize ALL roads
        # ====================================================

        roads = {}

        for road_id in road_edges:

            roads[road_id] = {
                "vehicle_count": 0,
                "total_speed": 0.0,
                "total_waiting": 0.0,
                "stopped_vehicles": 0
            }


        # ====================================================
        # Collect vehicle information
        # ====================================================

        vehicle_ids = traci.vehicle.getIDList()

        for vehicle_id in vehicle_ids:

            road_id = traci.vehicle.getRoadID(
                vehicle_id
            )

            # Ignore internal junction edges
            if road_id.startswith(":"):
                continue

            # Safety check
            if road_id not in roads:
                continue

            speed = traci.vehicle.getSpeed(
                vehicle_id
            )

            waiting_time = traci.vehicle.getWaitingTime(
                vehicle_id
            )


            # ----------------------------------------------
            # Update road statistics
            # ----------------------------------------------

            roads[road_id]["vehicle_count"] += 1

            roads[road_id]["total_speed"] += speed

            roads[road_id]["total_waiting"] += waiting_time


            if speed < STOP_SPEED:

                roads[road_id]["stopped_vehicles"] += 1


        # ====================================================
        # Save road-level records
        # ====================================================

        for road_id in road_edges:

            data = roads[road_id]

            vehicle_count = data["vehicle_count"]

            road_length = road_lengths.get(
                road_id,
                0.0
            )


            # ----------------------------------------------
            # Average speed
            # ----------------------------------------------

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


            # ----------------------------------------------
            # Density
            # ----------------------------------------------

            if road_length > 0:

                density = (
                    vehicle_count
                    / (road_length / 1000)
                )

            else:

                density = 0.0


            # ----------------------------------------------
            # Queue length estimate
            # ----------------------------------------------

            queue_length = (
                data["stopped_vehicles"]
                * AVERAGE_VEHICLE_LENGTH
            )


            # ----------------------------------------------
            # Write row
            # ----------------------------------------------

            writer.writerow([
                SCENARIO,
                step,
                road_id,
                round(road_length, 2),
                vehicle_count,
                round(average_speed_kmh, 2),
                data["stopped_vehicles"],
                round(average_waiting_time, 2),
                round(density, 2),
                round(queue_length, 2)
            ])


        # ====================================================
        # Progress
        # ====================================================

        if step % 10 == 0:

            active_roads = sum(
                1
                for road_id in road_edges
                if roads[road_id]["vehicle_count"] > 0
            )

            print(
                f"Step: {step:4d} | "
                f"Vehicles: {len(vehicle_ids):4d} | "
                f"Active roads: {active_roads:4d} | "
                f"Total roads: {len(road_edges):4d}"
            )


# ============================================================
# CLOSE SUMO
# ============================================================

traci.close()


print("\n========================================")
print(" Simulation finished")
print(" TraCI connection closed")
print(" Dataset saved:")
print(f" {output_file}")
print("========================================")