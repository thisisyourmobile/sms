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
            return requests.post(url, headers=headers, data=json.dumps(data) if data else requests.post(url, headers=headers)
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

def claim_gift(auth):
    """Claim daily gift if available"""
    response = make_api_request('https://api.chickcoop.io/gift/claim', auth)
    return response.status_code == 200 if response else False

def upgrade_laboratory(auth, research_type):
    """Upgrade specified laboratory research"""
    response = make_api_request('https://api.chickcoop.io/laboratory/research', auth, data={"researchType": research_type})
    if response and response.ok:
        upgrade_counts[research_type.split('.')[-1]] += 1
        return True
    return False

def sell_eggs(auth, quantity):
    """Sell specified quantity of eggs"""
    return make_api_request('https://api.chickcoop.io/user/sell-eggs', auth, data={"numberOfEggs": quantity})

# ========== ACCOUNT MANAGEMENT ========== #
def process_account(auth, index):
    """Handle all operations for a single account"""
    global last_update
    
    try:
        # Get account data
        response = make_api_request('https://api.chickcoop.io/hatch/manual', auth)
        if not response or response.status_code == 401:
            return f"{Fore.RED}Akun {index+1}: Auth failed"
            
        data = response.json()['data']
        profile = data['profile']
        stats = {
            'chickens': int(data['chickens']['quantity']),
            'eggs': int(data['eggs']['quantity']),
            'cash': f"{data['cash']:,.0f}".replace(",", "."),
            'gems': data['gem'],
            'level': data['discovery']['level'],
            'can_upgrade': data['discovery']['availableToUpgrade'],
            'capacity': data['farmCapacity']['capacity']
        }
        
        # Claim gift if available
        if claim_gift(auth):
            previous_results['chests'] = previous_results.get('chests', 0) + 1
        
        # Auto-upgrade logic
        chicken_percent = (stats['chickens'] / stats['capacity']) * 100
        if chicken_percent >= FARM_CAPACITY_THRESHOLD:
            upgrade_laboratory(auth, "laboratory.regular.farmCapacity")
        if stats['can_upgrade']:
            make_api_request('https://api.chickcoop.io/discovery/upgrade-eggs', auth)
        if stats['eggs'] > MIN_EGGS_FOR_SALE:
            sell_eggs(auth, stats['eggs'])
        
        # Format status line
        color = get_random_color()
        return (
            f"Akun {color}{index+1}{Style.RESET_ALL} | "
            f"🐔 {color}{stats['chickens']} ({chicken_percent:.0f}%) | "
            f"🥚 {color}{stats['eggs']} | "
            f"💰 {color}{stats['cash']} | "
            f"💎 {color}{stats['gems']} | "
            f"🎁 {color}{previous_results.get('chests', 0)} | "
            f"⬆️ {color}{upgrade_counts['egg_value']}/{upgrade_counts['laying_rate']}/{upgrade_counts['farm_capacity']}"
        )
        
    except Exception as e:
        print(f"{Fore.RED}Account {index+1} error: {e}")
        return None

# ========== WEB SERVER ENDPOINTS ========== #
@app.route('/')
def dashboard():
    """Main status dashboard"""
    global last_update
    return f"""
    <h1>🐔 Chickcoop Bot</h1>
    <p>🟢 Status: <strong>Running</strong></p>
    <p>👥 Accounts: <strong>{len(authorizations)}</strong></p>
    <p>🔄 Last Update: <strong>{last_update.strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
    <p>⏳ Next Spin: <strong>{next_spin_time.strftime('%H:%M:%S')}</strong></p>
    <p><a href="/health">Health Check</a></p>
    """

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "accounts": len(authorizations),
        "last_update": last_update.isoformat(),
        "next_spin": next_spin_time.isoformat(),
        "upgrades": upgrade_counts
    }), 200

# ========== MAIN BOT LOOP ========== #
def bot_cycle():
    """Main execution cycle with active/rest periods"""
    global next_spin_time, last_update
    
    while True:
        # Active period
        active_end = datetime.now() + ACTIVE_DURATION
        print(f"\n{Fore.GREEN}🚀 ACTIVE PERIOD | Until: {active_end.strftime('%H:%M:%S')}")
        
        while datetime.now() < active_end:
            try:
                # Handle wheel spins
                if datetime.now() >= next_spin_time:
                    print(f"{Fore.CYAN}🌀 Spinning wheels...")
                    with ThreadPoolExecutor() as executor:
                        results = executor.map(spin_wheel, authorizations, range(len(authorizations)))
                    next_spin_time = datetime.now() + timedelta(hours=1)
                
                # Process all accounts
                account_status = []
                with ThreadPoolExecutor(max_workers=len(authorizations)) as executor:
                    account_status = list(executor.map(process_account, authorizations, range(len(authorizations))))
                
                # Display results
                if any(account_status):
                    print("\033c", end="")  # Clear console
                    print("\n".join(filter(None, account_status)))
                    last_update = datetime.now()
                
                time.sleep(2)
                
            except Exception as e:
                print(f"{Fore.RED}⚠️ Cycle error: {e}")
                time.sleep(10)
        
        # Rest period
        rest_end = datetime.now() + REST_DURATION
        print(f"\n{Fore.YELLOW}😴 REST PERIOD | Until: {rest_end.strftime('%H:%M:%S')}")
        while datetime.now() < rest_end:
            time.sleep(1)

# ========== APPLICATION STARTUP ========== #
if __name__ == "__main__":
    # Start bot in background thread
    threading.Thread(target=bot_cycle, daemon=True).start()
    
    # Start Flask web server
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
