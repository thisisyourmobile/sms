import os
import time
import json
import random
import threading
from datetime import datetime, timedelta
from flask import Flask, Response
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ✅ Load authorization tokens
with open("query.txt", "r") as f:
    authorizations = [line.strip() for line in f if line.strip()]

status_log = []
next_phase_time = None
is_resting = False

def get_headers(auth):
    return {
        'accept': '*/*',
        'authorization': auth,
        'content-type': 'application/octet-stream',
        'origin': 'https://game.chickcoop.io',
        'referer': 'https://game.chickcoop.io/',
        'user-agent': 'Mozilla/5.0'
    }

def spin_wheel(auth, index):
    headers = get_headers(auth)
    data = json.dumps({"mode": "free"})
    try:
        r = requests.post('https://api.chickcoop.io/v2/wheel/spin', headers=headers, data=data)
        if r.status_code == 200:
            reward = r.json()['data']['wheelState'].get('availableReward')
            if reward:
                requests.post('https://api.chickcoop.io/wheel/claim', headers=headers)
                return f"[Akun {index+1}] 🎡 Wheel: {reward['text']} | {reward['type']} | {reward['amount']}"
    except Exception as e:
        return f"[Akun {index+1}] ❌ Spin error: {e}"
    return None

def claim_gift(auth, index):
    headers = get_headers(auth)
    try:
        r = requests.post('https://api.chickcoop.io/gift/claim', headers=headers)
        if r.status_code == 200 and r.json().get('ok'):
            return f"[Akun {index+1}] 🎁 Gift claimed successfully"
        return f"[Akun {index+1}] 🎁 No gift available"
    except Exception as e:
        return f"[Akun {index+1}] ❌ Gift error: {e}"

def fetch_user(auth, index):
    headers = get_headers(auth)
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
    global next_phase_time, is_resting
    print("🔁 Bot started — 1 hour active, 30 minutes rest cycles...\n")

    while True:
        # === ACTIVE PHASE (1 hour) ===
        is_resting = False
        next_phase_time = datetime.now() + timedelta(hours=1)

        while datetime.now() < next_phase_time:
            logs = []

            for idx, auth in enumerate(authorizations):
                # Spin wheel
                result = spin_wheel(auth, idx)
                if result:
                    logs.append(result)

                # Claim gift
                gift_result = claim_gift(auth, idx)
                logs.append(gift_result)

            with ThreadPoolExecutor() as exec:
                futures = [exec.submit(fetch_user, auth, idx) for idx, auth in enumerate(authorizations)]
                for f in futures:
                    result = f.result()
                    if result:
                        logs.append(result)

            status_log.clear()
            status_log.extend(logs)
            print("\n".join(logs), flush=True)
            time.sleep(10)

        # === REST PHASE (30 minutes) ===
        is_resting = True
        next_phase_time = datetime.now() + timedelta(minutes=30)
        status_log.clear()
        rest_msg = f"🛌 Bot is resting until {next_phase_time.strftime('%H:%M:%S')}"
        print(rest_msg, flush=True)
        status_log.append(rest_msg)

        while datetime.now() < next_phase_time:
            time.sleep(5)

@app.route("/")
def homepage():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rest_status = "✅ Running" if not is_resting else "🛌 Resting"
    remaining = (next_phase_time - datetime.now()).seconds // 60 if next_phase_time else 0
    html = f"<h2>{rest_status}</h2><p>⏱ Next phase in: {remaining} minutes</p><pre>{chr(10).join(status_log)}</pre>"
    return Response(html, mimetype="text/html")

# Start bot in background
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
