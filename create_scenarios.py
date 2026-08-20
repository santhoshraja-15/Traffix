import os
import re
import shutil

# ============================================================
# TRAFFICX - Traffic Scenario Generator
# ============================================================
#
# Creates four traffic-demand scenarios:
#
#   LOW
#   MEDIUM
#   HIGH
#   CONGESTED
#
# Simulation step length is explicitly fixed at:
#   1 second
#
# Therefore:
#   300 simulation steps = 5 minutes
#
# ============================================================


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = r"D:\TRAFFICX\2026-08-19-23-26-46"

NETWORK_FILE = "osm.net.xml.gz"

ADDITIONAL_FILES = "osm.poly.xml.gz,output.add.xml"

SOURCE_FILE = os.path.join(
    BASE_DIR,
    "osm.passenger.trips.xml"
)

SCENARIO_DIR = r"D:\TRAFFICX\scenarios"


# ============================================================
# SCENARIO DEFINITIONS
# ============================================================
#
# LOW:
#   Keep every second trip.
#
# MEDIUM:
#   Keep all trips at original departure times.
#
# HIGH:
#   Keep all trips and compress departure times.
#
# CONGESTED:
#   Keep all trips and compress departure times even more.
#
# ============================================================

scenarios = {

    "low": {
        "mode": "sample",
        "sample_every": 2,
        "time_scale": 1.0
    },

    "medium": {
        "mode": "all",
        "sample_every": 1,
        "time_scale": 1.0
    },

    "high": {
        "mode": "all",
        "sample_every": 1,
        "time_scale": 0.60
    },

    "congested": {
        "mode": "all",
        "sample_every": 1,
        "time_scale": 0.35
    }

}


# ============================================================
# CREATE SCENARIO DIRECTORY
# ============================================================

os.makedirs(
    SCENARIO_DIR,
    exist_ok=True
)


# ============================================================
# CHECK SOURCE FILE
# ============================================================

if not os.path.exists(SOURCE_FILE):

    raise FileNotFoundError(
        f"\nSource trip file not found:\n"
        f"{SOURCE_FILE}"
    )


# ============================================================
# READ ORIGINAL TRIP FILE
# ============================================================

with open(
    SOURCE_FILE,
    "r",
    encoding="utf-8"
) as f:

    lines = f.readlines()


# ============================================================
# HEADER
# ============================================================

print("\n========================================")
print(" TRAFFICX - SCENARIO GENERATOR")
print("========================================")

print("\nSource:")
print(SOURCE_FILE)

print("\nSimulation configuration:")
print("Step length : 1 second")
print("5 minutes   : 300 steps")


# ============================================================
# PROCESS EACH SCENARIO
# ============================================================

for scenario_name, config in scenarios.items():

    print("\n----------------------------------------")
    print(
        f"Creating {scenario_name.upper()} scenario..."
    )
    print("----------------------------------------")


    # --------------------------------------------------------
    # Scenario directory
    # --------------------------------------------------------

    scenario_path = os.path.join(
        SCENARIO_DIR,
        scenario_name
    )

    os.makedirs(
        scenario_path,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Output files
    # --------------------------------------------------------

    output_trip_file = os.path.join(
        scenario_path,
        "traffic.trips.xml"
    )

    output_config_file = os.path.join(
        scenario_path,
        "traffic.sumocfg"
    )


    # --------------------------------------------------------
    # Process trips
    # --------------------------------------------------------

    trip_count = 0

    kept_trip_count = 0

    output_lines = []


    for line in lines:

        # ----------------------------------------------------
        # Keep XML lines that aren't trips unchanged
        # ----------------------------------------------------

        if not line.strip().startswith("<trip "):

            output_lines.append(line)

            continue


        # ----------------------------------------------------
        # LOW scenario:
        #
        # Keep every second trip.
        # ----------------------------------------------------

        if (
            config["mode"] == "sample"
            and
            trip_count % config["sample_every"] != 0
        ):

            trip_count += 1

            continue


        # ----------------------------------------------------
        # Modify departure time
        # ----------------------------------------------------

        match = re.search(
            r'depart="([0-9.]+)"',
            line
        )


        if match:

            original_depart = float(
                match.group(1)
            )


            new_depart = (
                original_depart
                * config["time_scale"]
            )


            line = re.sub(
                r'depart="[0-9.]+"',
                f'depart="{new_depart:.2f}"',
                line,
                count=1
            )


        # ----------------------------------------------------
        # Keep modified trip
        # ----------------------------------------------------

        output_lines.append(line)

        trip_count += 1

        kept_trip_count += 1


    # ========================================================
    # WRITE TRIP FILE
    # ========================================================

    with open(
        output_trip_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.writelines(output_lines)


    # ========================================================
    # CREATE SUMO CONFIGURATION
    # ========================================================
    #
    # IMPORTANT:
    #
    # step-length = 1 second
    #
    # This makes:
    #
    # 1 step   = 1 second
    # 60 steps = 1 minute
    # 300 steps = 5 minutes
    #
    # ========================================================

    config_text = f"""<?xml version="1.0" encoding="UTF-8"?>

<sumoConfiguration
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">

    <input>
        <net-file value="{NETWORK_FILE}"/>
        <route-files value="traffic.trips.xml"/>
        <additional-files value="{ADDITIONAL_FILES}"/>
    </input>

    <time>
        <step-length value="1"/>
    </time>

    <output>
        <tripinfo-output value="tripinfos.xml"/>
        <statistic-output value="stats.xml"/>
    </output>

    <processing>
        <ignore-route-errors value="true"/>
        <tls.actuated.jam-threshold value="30"/>
    </processing>

    <routing>
        <device.rerouting.adaptation-steps value="18"/>
        <device.rerouting.adaptation-interval value="10"/>
    </routing>

    <report>
        <verbose value="false"/>
        <duration-log.statistics value="true"/>
        <no-step-log value="true"/>
    </report>

</sumoConfiguration>
"""


    # ========================================================
    # WRITE SUMO CONFIG
    # ========================================================

    with open(
        output_config_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(config_text)


    # ========================================================
    # COPY REQUIRED NETWORK FILES
    # ========================================================

    required_files = [
        "osm.net.xml.gz",
        "osm.poly.xml.gz",
        "output.add.xml"
    ]


    for filename in required_files:

        source = os.path.join(
            BASE_DIR,
            filename
        )

        destination = os.path.join(
            scenario_path,
            filename
        )


        if not os.path.exists(source):

            raise FileNotFoundError(
                f"\nRequired file not found:\n"
                f"{source}"
            )


        shutil.copy2(
            source,
            destination
        )


    # ========================================================
    # SCENARIO SUMMARY
    # ========================================================

    print(
        f"Scenario      : "
        f"{scenario_name.upper()}"
    )

    print(
        f"Trips kept    : "
        f"{kept_trip_count}"
    )

    print(
        f"Time scale    : "
        f"{config['time_scale']}"
    )

    print(
        f"Trip file     : "
        f"{output_trip_file}"
    )

    print(
        f"SUMO config   : "
        f"{output_config_file}"
    )


# ============================================================
# COMPLETE
# ============================================================

print("\n========================================")
print(" Scenario generation complete!")
print("========================================")

print("\nCreated:")

print(
    SCENARIO_DIR
)

print("\nScenarios:")

print("  LOW")
print("  MEDIUM")
print("  HIGH")
print("  CONGESTED")

print("\nSimulation timing:")

print("  1 step   = 1 second")
print("  60 steps = 1 minute")
print("  300 steps = 5 minutes")

print("\n========================================")