import os
import sys
import csv
import traci


# ============================================================
# TRAFFICX - MULTI-SCENARIO TRAFFIC DATA COLLECTOR
# ============================================================

if "SUMO_HOME" not in os.environ:
    sys.exit("SUMO_HOME environment variable is not set.")


SUMO_BINARY = os.path.join(
    os.environ["SUMO_HOME"],
    "bin",
    "sumo.exe"
)


BASE_DIR = r"D:\TRAFFICX\scenarios"
OUTPUT_DIR = r"D:\TRAFFICX"


SCENARIOS = [
    "low",
    "medium",
    "high",
    "congested"
]


# ============================================================
# RUN ONE SCENARIO
# ============================================================

def run_scenario(scenario):

    print("\n")
    print("========================================")
    print(f" TRAFFICX - {scenario.upper()} SCENARIO")
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
        f"traffic_{scenario}.csv"
    )

    print(f"Config : {sumo_config}")
    print(f"Output : {output_file}")

    # --------------------------------------------------------
    # Start SUMO through TraCI
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
    # Create dataset
    # --------------------------------------------------------

    with open(
        output_file,
        "w",
        newline=""
    ) as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "step",
            "vehicle_count",
            "average_speed_kmh",
            "stopped_vehicles",
            "average_waiting_time",
            "active_roads"
        ])

        # ----------------------------------------------------
        # Run simulation
        # ----------------------------------------------------

        for step in range(1000):

            traci.simulationStep()

            vehicle_ids = traci.vehicle.getIDList()

            total_vehicles = len(vehicle_ids)

            total_speed = 0.0
            total_waiting = 0.0

            stopped_vehicles = 0

            active_roads = set()

            # ------------------------------------------------
            # Collect vehicle information
            # ------------------------------------------------

            for vehicle_id in vehicle_ids:

                speed = traci.vehicle.getSpeed(
                    vehicle_id
                )

                waiting_time = traci.vehicle.getWaitingTime(
                    vehicle_id
                )

                road_id = traci.vehicle.getRoadID(
                    vehicle_id
                )

                total_speed += speed
                total_waiting += waiting_time

                active_roads.add(road_id)

                if speed < (5 / 3.6):

                    stopped_vehicles += 1

            # ------------------------------------------------
            # Calculate averages
            # ------------------------------------------------

            if total_vehicles > 0:

                average_speed = (
                    total_speed /
                    total_vehicles
                ) * 3.6

                average_waiting = (
                    total_waiting /
                    total_vehicles
                )

            else:

                average_speed = 0.0
                average_waiting = 0.0

            # ------------------------------------------------
            # Save
            # ------------------------------------------------

            writer.writerow([
                step,
                total_vehicles,
                round(average_speed, 2),
                stopped_vehicles,
                round(average_waiting, 2),
                len(active_roads)
            ])

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            if step % 100 == 0:

                print(
                    f"Step: {step:4d} | "
                    f"Vehicles: {total_vehicles:4d} | "
                    f"Avg Speed: {average_speed:6.2f} km/h | "
                    f"Stopped: {stopped_vehicles:3d} | "
                    f"Waiting: {average_waiting:6.2f}s | "
                    f"Roads: {len(active_roads):3d}"
                )

    # --------------------------------------------------------
    # Close SUMO
    # --------------------------------------------------------

    traci.close()

    print("\nScenario finished!")

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
 MULTI-SCENARIO EXPERIMENT
========================================
""")

for scenario in SCENARIOS:

    run_scenario(
        scenario
    )


print("""
========================================
 ALL SCENARIOS COMPLETE
========================================

Generated:

traffic_low.csv
traffic_medium.csv
traffic_high.csv
traffic_congested.csv
""")