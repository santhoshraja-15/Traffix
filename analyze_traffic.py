import pandas as pd

file_path = r"D:\TRAFFICX\traffic_data.csv"

df = pd.read_csv(file_path)

print("\n========================================")
print(" TRAFFICX - DATASET ANALYSIS")
print("========================================")

print(f"\nNumber of records: {len(df)}")

print("\nColumns:")
for column in df.columns:
    print(f" - {column}")

print("\n----------------------------------------")
print(" BASIC STATISTICS")
print("----------------------------------------")

print(f"Minimum vehicles     : {df['vehicle_count'].min()}")
print(f"Maximum vehicles     : {df['vehicle_count'].max()}")

print(
    f"Average vehicles     : "
    f"{df['vehicle_count'].mean():.2f}"
)

print(
    f"Minimum speed        : "
    f"{df['average_speed_kmh'].min():.2f} km/h"
)

print(
    f"Maximum speed        : "
    f"{df['average_speed_kmh'].max():.2f} km/h"
)

print(
    f"Average speed        : "
    f"{df['average_speed_kmh'].mean():.2f} km/h"
)

print(
    f"Maximum stopped      : "
    f"{df['stopped_vehicles'].max()}"
)

print(
    f"Maximum waiting time : "
    f"{df['average_waiting_time'].max():.2f} s"
)

print(
    f"Average waiting time : "
    f"{df['average_waiting_time'].mean():.2f} s"
)

print(
    f"Maximum active roads : "
    f"{df['active_roads'].max()}"
)

print("\n----------------------------------------")
print(" LAST 10 RECORDS")
print("----------------------------------------")

print(df.tail(10).to_string(index=False))

print("\n========================================")
print(" Analysis complete")
print("========================================")