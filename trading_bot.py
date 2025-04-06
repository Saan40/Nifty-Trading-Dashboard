import pandas as pd
import requests
from datetime import datetime
import time
import logging
import json
import pyotp
import threading

from SmartApi.smartConnect import SmartConnect
from SmartApi.smartApiWebsocket import SmartWebSocket  # Correct import with capital S and A

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("SmartApi imports working fine and bot is starting...")

if __name__ == "__main__":
    main()
