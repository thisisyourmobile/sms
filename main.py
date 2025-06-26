import os
import time
import json
import random
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, Response
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Store results globally for web display
status_log = []
next_rest_time = None
is_resting = False

# Read token
with open("query.txt", "r") as f:
    authorizations = [line.strip() for line in f if line.strip()]

upgrade_counts = {"egg_value": 0, "laying_rate": 0}
previous_results = {}

def spin_wheel(auth, index):
    headers = {'authorization': auth}
    data = json.dumps({"mode": "free"})
    try:
        r = requests.post('https://api.chickcoop.io/v2/wheel/spin', headers=headers, data=data)
        if r.status_code == 200:
            reward = r.json()['data']['wheelState'].get('availableReward')
            if reward:
                requests.post('https://api.chickcoop.io/wheel/claim', headers=headers)
                return f"[Akun {index+1}] Wheel: {reward['text']} | {reward['type']} | {reward['amount']}"
    except Exception as e:
        return f"[Akun {index+1}] Spin error: {e}"
    return None

def fetch_user(auth, index):
    headers = {'authorization': auth}
    try:
        r = requests.post("https://api.chickcoop.io/hatch/manual", headers=headers)
        if r.status_code == 401:
            return f"[Akun {index+1}] ❌ Authorization failed"
        data = r.json()['data']
        chickens = data['chickens']['quantity']
        eggs = data['eggs']['quantity']
        cash = data['cash']
        gem = data['gem']
        level = data['discovery']['level']
        name = data['profile']['username']
        farm_capacity = data['farmCapacity']['capacity']
        if eggs > 100:
            requests.post('https://api.chickcoop.io/user/sell-eggs',
                          headers=headers, data=json.dumps({"numberOfEggs": eggs}))
        return (f"[Akun {index+1}] 🐔 {name} | Level: {level} | Chickens: {chickens} | "
                f"Eggs: {eggs} | Cash: {cash} | Gems: {gem}")
    except Exception as e:
        return f"[Akun {index+1}] ❌ Error: {e}"

def bot_loop():
    global next_rest_time, is_resting
    print("🔁 Bot started — running 1h, resting 30m...\n")
    while True:
        run_until = datetime.now() + timedelta(hours=1)
        next_rest_time = run_until

        while datetime.now() < run_until:
            is_resting = False
            logs = []

            # Spin if due
            for idx, auth in enumerate(authorizations):
                result = spin_wheel(auth, idx)
                if result:
                    logs.append(result)

            # Hatch/update all accounts
            with ThreadPoolExecutor() as exec:
                futures = [exec.submit(fetch_user, auth, idx) for idx, auth in enumerate(authorizations)]
                for f in futures:
                    result = f.result()
                    if result:
                        logs.append(result)

            # Save logs for web
            status_log.clear()
            status_log.extend(logs)
            print("\n".join(logs), flush=True)
            time.sleep(10)

        # Sleep 30 min
        is_resting = True
        next_rest_time = datetime.now() + timedelta(minutes=30)
        status_log.clear()
        status_log.append(f"🛌 Bot is resting... until {next_rest_time.strftime('%H:%M:%S')}")
        print(status_log[-1], flush=True)
        time.sleep(1800)

@app.route("/")
def homepage():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rest_status = "✅ Running" if not is_resting else "🛌 Resting"
    remaining = (next_rest_time - datetime.now()).seconds // 60 if next_rest_time else 0
    html = f"<h2>{rest_status}</h2><p>⏱ Next phase in: {remaining} minutes</p><pre>{chr(10).join(status_log)}</pre>"
    return Response(html, mimetype="text/html")

# Start bot in background thread
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
