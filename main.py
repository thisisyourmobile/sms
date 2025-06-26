import os
import requests
import time
import json
from colorama import init, Fore, Style
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from flask import Flask, jsonify
import threading

# Initialize colorama and Flask
init(autoreset=True)
app = Flask(__name__)

# ========== CONFIGURATION ========== #
ACTIVE_DURATION = timedelta(hours=1)    # 1 hour active
REST_DURATION = timedelta(minutes=30)   # 30 minutes rest
MIN_EGGS_FOR_SALE = 100                 # Minimum eggs to trigger sale
FARM_CAPACITY_THRESHOLD = 90            # Percentage to trigger capacity upgrade

# ========== BOT CORE FUNCTIONS ========== #
def get_random_color():
    """Return a random console color"""
    colors = [Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    return random.choice(colors)

def load_authorizations():
    """Load authorization tokens from query.txt"""
    with open('query.txt', 'r') as file:
        return [line.strip() for line in file if line.strip()]

# Global variables
authorizations = load_authorizations()
previous_results = {}
upgrade_counts = {"egg_value": 0, "laying_rate": 0, "farm_capacity": 0}
next_spin_time = datetime.now()
last_update = datetime.now()

# ========== API OPERATIONS ========== #
def make_api_request(url, auth, method='POST', data=None):
    """Generic API request handler"""
    headers = {
        'authorization': auth,
        'content-type': 'application/octet-stream',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    try:
        if method == 'POST':
            if data:
                return requests.post(url, headers=headers, data=json.dumps(data))
            return requests.post(url, headers=headers)
        return requests.get(url, headers=headers)
    except Exception as e:
        print(f"{Fore.RED}API Error: {e}")
        return None

def spin_wheel(auth, index):
    """Handle wheel spin and reward claiming"""
    global next_spin_time
    response = make_api_request('https://api.chickcoop.io/v2/wheel/spin', auth, data={"mode": "free"})
    
    if response and response.status_code == 200:
        wheel_state = response.json().get('data', {}).get('wheelState', {})
        if wheel_state.get('availableReward'):
            reward = wheel_state['availableReward']
            print(f"{Fore.CYAN}Akun {index}: Won {reward['amount']} {reward['text']}")
            make_api_request('https://api.chickcoop.io/wheel/claim', auth)
        else:
            next_spin = datetime.fromtimestamp(wheel_state.get('nextTimeFreeSpin', 0) / 1000)
            print(f"{Fore.YELLOW}Akun {index}: Next spin at {next_spin.strftime('%H:%M')}")
        return True
    return False

# [Rest of your functions remain unchanged...]

# ========== APPLICATION STARTUP ========== #
if __name__ == "__main__":
    # Start bot in background thread
    threading.Thread(target=bot_cycle, daemon=True).start()
    
    # Start Flask web server
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
