import os
import sys
import traci

# Path to SUMO
if "SUMO_HOME" not in os.environ:
    sys.exit("Please set the SUMO_HOME environment variable.")

sumo_binary = os.path.join(
    os.environ["SUMO_HOME"],
    "bin",
    "sumo-gui.exe"
)

# SUMO configuration file
sumo_config = r"D:\TRAFFICX\2026-08-19-23-26-46\osm.sumocfg"

# Start SUMO
traci.start([
    sumo_binary,
    "-c",
    sumo_config
])

print("Connected to SUMO successfully!")

# Run the simulation
step = 0

while step < 100:
    traci.simulationStep()

    # Get all vehicles currently in the simulation
    vehicle_ids = traci.vehicle.getIDList()

    print(
        f"Step: {step:3d} | "
        f"Vehicles: {len(vehicle_ids)}"
    )

    step += 1

# Close SUMO
traci.close()

print("Simulation finished.")