import json

# Exchange rate: 1 GP = 0.000000025 USD
GP_TO_USD_RATE = 0.0000000264

# Load the JSON file
with open(".json/currency.json", "r") as file:
    currency_data = json.load(file)

# Convert each balance from GP to USD
usd_values = {user_id: gp_balance * GP_TO_USD_RATE for user_id, gp_balance in currency_data.items()}

# Print results
for user, usd in usd_values.items():
    print(f"User {user}: {usd:.2f} USD")

# (Optional) Save the converted values to a new JSON file
with open("currency_usd.json", "w") as file:
    json.dump(usd_values, file, indent=4)
