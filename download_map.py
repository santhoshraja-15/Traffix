import requests

url = "https://overpass-api.de/api/map?bbox=80.200,13.080,80.230,13.110"

print("Downloading OpenStreetMap data...")

response = requests.get(url, timeout=120)
response.raise_for_status()

with open("anna_nagar.osm", "wb") as f:
    f.write(response.content)

print("Download complete!")
print(f"File size: {len(response.content) / 1024 / 1024:.2f} MB")