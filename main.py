from flask import Flask, request, jsonify
import requests  # For calling DeepSeek API

app = Flask(__name__)

# 🔑 DeepSeek API Configuration
DEEPSEEK_API_KEY = "sk-9efc6cf0f33349ac9d747c267c74d62b"  # Replace with your key
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Verify latest URL

@app.route('/sms', methods=['GET', 'POST'])
def sms_reply():
    # Extract sender and message
    sender = request.values.get('sender', 'Unknown')
    message = request.values.get('message')
    
    if not message:
        return jsonify({'reply': "No message received."})

    try:
        # Call DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",  # Verify correct model name
            "messages": [
                {"role": "system", "content": "Reply in 1 SMS (max 160 chars). Be concise."},
                {"role": "user", "content": f"{sender} wrote: {message}"}
            ],
            "max_tokens": 100
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTP errors
        
        reply = response.json()["choices"][0]["message"]["content"].strip()[:160]
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'reply': "Sorry, I couldn't process that."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
