import pandas as pd
import requests

# Angel One instrument list URL (FnO)
url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

print("Downloading instruments list from Angel One...")
response = requests.get(url)
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data)

# Optional: filter only NIFTY and BANKNIFTY if needed
fno_df = df[df["name"].isin(["NIFTY", "BANKNIFTY"])]

# Save to CSV
fno_df.to_csv("instruments.csv", index=False)
print("instruments.csv generated with", len(fno_df), "rows.")
