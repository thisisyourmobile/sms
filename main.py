import os
import requests
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# Read and parse the query.txt file
with open('query.txt', 'r') as file:
    lines = file.readlines()
authorizations = [line.strip() for line in lines]

previous_results = {}
upgrade_counts = {
    "egg_value": 0,
    "laying_rate": 0
}

def spin_wheel(auth, index):
    headers = {
        'authorization': auth,
        'origin': 'https://game.chickcoop.io',
        'referer': 'https://game.chickcoop.io/',
        'user-agent': 'Mozilla/5.0'
    }
    data = json.dumps({"mode": "free"})
    response = requests.post('https://api.chickcoop.io/v2/wheel/spin', headers=headers, data=data)
    
    if response.status_code == 200:
        response_data = response.json()
        wheel_state = response_data.get('data', {}).get('wheelState', {})
        
        if wheel_state.get('availableReward'):
            reward = wheel_state['availableReward']
            print(f"[Akun {index+1}] Wheel reward: {reward['text']} | {reward['type']} | {reward['amount']}")
            claim = requests.post('https://api.chickcoop.io/wheel/claim', headers=headers)
            if claim.status_code == 200:
                print(f"[Akun {index+1}] Reward claimed.")
            else:
                print(f"[Akun {index+1}] Claim failed.")
        else:
            print(f"[Akun {index+1}] No reward available.")
        return True
    return False

def claim_gift(auth):
    headers = {'authorization': auth}
    r = requests.post('https://api.chickcoop.io/gift/claim', headers=headers)
    return r.status_code == 200 and r.json().get('ok')

def upgrade_laboratory(auth, research_type):
    headers = {'authorization': auth}
    data = json.dumps({"researchType": research_type})
    r = requests.post('https://api.chickcoop.io/laboratory/research', headers=headers, data=data)
    return r.json()

def upgrade_farm(auth):
    headers = {'authorization': auth}
    return requests.post('https://api.chickcoop.io/discovery/upgrade-eggs', headers=headers).json()

def sell_eggs(auth, number):
    headers = {'authorization': auth}
    data = json.dumps({"numberOfEggs": number})
    r = requests.post('https://api.chickcoop.io/user/sell-eggs', headers=headers, data=data)
    return r.status_code == 200

def fetch_and_print_user_data(auth, index):
    headers = {'authorization': auth}
    try:
        r = requests.post('https://api.chickcoop.io/hatch/manual', headers=headers)
        if r.status_code == 401:
            return f"[Akun {index+1}] Authorization failed."

        data = r.json()['data']
        profile = data['profile']
        chickens = data['chickens']
        eggs = data['eggs']
        cash = data['cash']
        gem = data['gem']
        level = data['discovery']['level']
        ready_upgrade = data['discovery']['availableToUpgrade']
        farm_capacity = data['farmCapacity']['capacity']

        chest_count = previous_results.get('chest_count', 0)
        if claim_gift(auth):
            chest_count += 1
            previous_results['chest_count'] = chest_count

        if upgrade_laboratory(auth, "laboratory.regular.eggValue").get("ok"):
            upgrade_counts["egg_value"] += 1
        if upgrade_laboratory(auth, "laboratory.regular.layingRate").get("ok"):
            upgrade_counts["laying_rate"] += 1

        chicken_count = int(chickens['quantity'])
        percentage = (chicken_count / farm_capacity) * 100

        result = (
            f"[Akun {index+1}] Name: {profile['username']} | "
            f"Chickens: {chicken_count} ({percentage:.0f}%) | "
            f"Level: {level} | Eggs: {int(eggs['quantity'])} | "
            f"Cash: {cash:,} | Gems: {gem} | Gifts: {chest_count} | "
            f"Upgrades - Egg: {upgrade_counts['egg_value']}, Lay: {upgrade_counts['laying_rate']}"
        )

        if chicken_count >= farm_capacity * 0.9:
            upgrade_laboratory(auth, "laboratory.regular.farmCapacity")
        if ready_upgrade:
            upgrade_farm(auth)
        if int(eggs['quantity']) > 100:
            sell_eggs(auth, int(eggs['quantity']))

        return result
    except Exception as e:
        return f"[Akun {index+1}] Error: {str(e)}"

# === Main bot loop with timing ===
RUN_DURATION = timedelta(hours=1)
REST_DURATION = timedelta(minutes=30)

print("🔁 Bot started — will run for 1 hour and sleep 30 minutes in cycles...\n")

while True:
    run_start = datetime.now()
    run_end = run_start + RUN_DURATION
    next_spin_time = datetime.now()

    while datetime.now() < run_end:
        results = []
        now = datetime.now()

        if now >= next_spin_time:
            for i, auth in enumerate(authorizations):
                spin_wheel(auth, i)
            next_spin_time = now + timedelta(hours=1)

        with ThreadPoolExecutor(max_workers=len(authorizations)) as executor:
            futures = [executor.submit(fetch_and_print_user_data, auth, i) for i, auth in enumerate(authorizations)]
            for future in futures:
                result = future.result()
                if result:
                    results.append(result)

        if results:
            print("\n".join(results), flush=True)

        time.sleep(5)

    print(f"\n🛌 Resting for 30 minutes... [{datetime.now().strftime('%H:%M:%S')}]\n", flush=True)
    time.sleep(REST_DURATION.total_seconds())
