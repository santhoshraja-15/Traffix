import os
import sys
import csv
import traci

# ============================================================
# TRAFFICX - Traffic Data Collector
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
output_file = r"D:\TRAFFICX\traffic_data.csv"


# ============================================================
# Start SUMO
# ============================================================

traci.start([
    sumo_binary,
    "-c",
    sumo_config
])

print("\n========================================")
print(" TRAFFICX - TRAFFIC DATA COLLECTOR")
print("========================================")
print("Connected to SUMO successfully!")
print(f"Dataset: {output_file}\n")


# ============================================================
# Create CSV file
# ============================================================

with open(output_file, "w", newline="") as csvfile:

    writer = csv.writer(csvfile)

    # CSV header
    writer.writerow([
        "step",
        "vehicle_count",
        "average_speed_kmh",
        "stopped_vehicles",
        "average_waiting_time",
        "active_roads"
    ])

    # ========================================================
    # Run simulation
    # ========================================================

    for step in range(1000):

        traci.simulationStep()

        vehicle_ids = traci.vehicle.getIDList()

        total_vehicles = len(vehicle_ids)

        total_speed = 0.0
        total_waiting = 0.0

        stopped_vehicles = 0

        active_roads = set()

        # ----------------------------------------------------
        # Collect vehicle information
        # ----------------------------------------------------

        for vehicle_id in vehicle_ids:

            speed = traci.vehicle.getSpeed(vehicle_id)

            waiting_time = traci.vehicle.getWaitingTime(
                vehicle_id
            )

            road_id = traci.vehicle.getRoadID(
                vehicle_id
            )

            total_speed += speed
            total_waiting += waiting_time

            active_roads.add(road_id)

            # Vehicle considered stopped below 5 km/h
            if speed < (5 / 3.6):
                stopped_vehicles += 1

        # ----------------------------------------------------
        # Calculate averages
        # ----------------------------------------------------

        if total_vehicles > 0:

            average_speed = (
                total_speed / total_vehicles
            ) * 3.6

            average_waiting = (
                total_waiting / total_vehicles
            )

        else:

            average_speed = 0.0
            average_waiting = 0.0

        # ----------------------------------------------------
        # Save data
        # ----------------------------------------------------

        writer.writerow([
            step,
            total_vehicles,
            round(average_speed, 2),
            stopped_vehicles,
            round(average_waiting, 2),
            len(active_roads)
        ])

        # Print progress every 10 steps
        if step % 10 == 0:

            print(
                f"Step: {step:4d} | "
                f"Vehicles: {total_vehicles:3d} | "
                f"Avg Speed: {average_speed:6.2f} km/h | "
                f"Stopped: {stopped_vehicles:3d} | "
                f"Waiting: {average_waiting:6.2f}s | "
                f"Roads: {len(active_roads):3d}"
            )


# ============================================================
# Close SUMO
# ============================================================

traci.close()

print("\n========================================")
print(" Simulation finished")
print(" TraCI connection closed")
print(f" Dataset saved to:")
print(f" {output_file}")
print("========================================")