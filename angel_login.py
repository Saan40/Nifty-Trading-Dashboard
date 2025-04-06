from smartapi.smartConnect import SmartConnect
import pyotp

def angel_login():
    # === Fill in your Angel One API details here ===
    api_key = "6z7qhWH4"
    client_id = "S1645433"       # e.g., "X12345"
    password = "8876"         # Angel One login password
    totp_secret = "CVJXSB4UTU5G7W662POTNI7GMU"   # The 16-digit key used in Google Authenticator

    try:
        obj = SmartConnect(api_key=api_key)

        # Generate TOTP
        totp = pyotp.TOTP(totp_secret).now()

        # Generate session and get tokens
        session_data = obj.generateSession(client_id, password, totp)

        access_token = session_data['data']['access_token']
        feed_token = obj.getfeedToken()

        print("[+] Angel One Login Successful")
        return obj, access_token, feed_token

    except Exception as e:
        print("[-] Login failed:", str(e))
        return None, None, None
