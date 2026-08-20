import os
import sys
import csv
import traci

# ============================================================
# TRAFFICX - Road-Level Traffic Data Collector
# ============================================================

if "SUMO_HOME" not in os.environ:
    sys.exit("SUMO_HOME environment variable is not set.")

sumo_binary = os.path.join(
    os.environ["SUMO_HOME"],
    "bin",
    "sumo-gui.exe"
)

sumo_config = r"D:\TRAFFICX\2026-08-19-23-26-46\osm.sumocfg"

# Output dataset
output_file = r"D:\TRAFFICX\road_level_traffic.csv"


# ============================================================
# Start SUMO
# ============================================================

traci.start([
    sumo_binary,
    "-c",
    sumo_config
])

print("\n========================================")
print(" TRAFFICX - ROAD LEVEL DATA COLLECTOR")
print("========================================")
print("Connected to SUMO successfully!")
print(f"Dataset: {output_file}\n")


# ============================================================
# Create CSV
# ============================================================

with open(output_file, "w", newline="") as csvfile:

    writer = csv.writer(csvfile)

    writer.writerow([
        "step",
        "road_id",
        "vehicle_count",
        "average_speed_kmh",
        "stopped_vehicles",
        "average_waiting_time",
        "road_length_m"
    ])

    # ========================================================
    # Run simulation
    # ========================================================

    for step in range(1000):

        traci.simulationStep()

        vehicle_ids = traci.vehicle.getIDList()

        # ----------------------------------------------------
        # Store information separately for each road
        # ----------------------------------------------------

        roads = {}

        for vehicle_id in vehicle_ids:

            road_id = traci.vehicle.getRoadID(vehicle_id)

            # Ignore internal SUMO edges
            if road_id.startswith(":"):
                continue

            speed = traci.vehicle.getSpeed(vehicle_id)

            waiting_time = traci.vehicle.getWaitingTime(
                vehicle_id
            )

            # Create road entry if not already present
            if road_id not in roads:

                roads[road_id] = {
                    "vehicle_count": 0,
                    "total_speed": 0.0,
                    "total_waiting": 0.0,
                    "stopped_vehicles": 0
                }

            # ----------------------------------------------
            # Update road statistics
            # ----------------------------------------------

            roads[road_id]["vehicle_count"] += 1

            roads[road_id]["total_speed"] += speed

            roads[road_id]["total_waiting"] += waiting_time

            # Vehicle considered stopped below 5 km/h
            if speed < (5 / 3.6):

                roads[road_id]["stopped_vehicles"] += 1

        # ----------------------------------------------------
        # Save one row for every active road
        # ----------------------------------------------------

        for road_id, data in roads.items():

            vehicle_count = data["vehicle_count"]

            if vehicle_count > 0:

                average_speed = (
                    data["total_speed"] / vehicle_count
                ) * 3.6

                average_waiting = (
                    data["total_waiting"] / vehicle_count
                )

            else:

                average_speed = 0.0
                average_waiting = 0.0

            # ------------------------------------------------
            # Get road length
            # ------------------------------------------------

            try:

                road_length = traci.lane.getLength(
                    road_id + "_0"
                )

            except:

                road_length = 0.0

            # ------------------------------------------------
            # Write row
            # ------------------------------------------------

            writer.writerow([
                step,
                road_id,
                vehicle_count,
                round(average_speed, 2),
                data["stopped_vehicles"],
                round(average_waiting, 2),
                round(road_length, 2)
            ])

        # ----------------------------------------------------
        # Progress information
        # ----------------------------------------------------

        if step % 10 == 0:

            print(
                f"Step: {step:4d} | "
                f"Vehicles: {len(vehicle_ids):4d} | "
                f"Active Roads: {len(roads):4d}"
            )


# ============================================================
# Close SUMO
# ============================================================

traci.close()

print("\n========================================")
print(" Simulation finished")
print(" TraCI connection closed")
print(" Road-level dataset saved:")
print(f" {output_file}")
print("========================================")