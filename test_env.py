from dotenv import load_dotenv
import os

load_dotenv()

print("Trading API Key:", os.getenv("TRADING_API_KEY"))
print("Trading API Secret:", os.getenv("TRADING_API_SECRET"))
print("Historical API Key:", os.getenv("HISTORICAL_API_KEY"))
print("Historical API Secret:", os.getenv("HISTORICAL_API_SECRET"))
print("Redirect URL:", os.getenv("REDIRECT_URL"))
print("Client ID:", os.getenv("CLIENT_ID"))
print("Password:", os.getenv("PASSWORD"))
print("TOTP Key:", os.getenv("TOTP_KEY"))
print("GNews API Key:", os.getenv("GNEWS_API_KEY"))
