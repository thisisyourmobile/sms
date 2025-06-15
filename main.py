from flask import Flask, request, jsonify
import openai
from datetime import datetime

app = Flask(__name__)

# 🔐 Credentials (used for basic auth)
USERNAME = "NEISYU"
PASSWORD = "12345678912345"

# 🔑 Your OpenAI API key
openai.api_key = "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"  # Replace with your actual key

@app.route('/')
def home():
    return "✅ SMS AI Chatbot is running!"

@app.route('/sms', methods=['POST'])
def sms_handler():
    # 🔐 Basic Authentication
    auth = request.authorization
    if not auth or auth.username != USERNAME or auth.password != PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401

    # 📥 Get incoming SMS
    sms_data = request.get_json() or request.form
    sender = sms_data.get('sender')
    message = sms_data.get('message')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not message:
        return jsonify({'error': 'Message is empty'}), 400

    print(f"[{timestamp}] Message from {sender}: {message}")

    # 🧠 Get AI response from OpenAI
    try:
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a helpful AI SMS assistant. Keep replies short and simple."},
                {"role": "user", "content": message}
            ]
        )
        reply = chat['choices'][0]['message']['content'].strip()
    except Exception as e:
        reply = f"AI Error: {str(e)}"

    # 📨 Send back the reply (to display or SMS app will use this)
    response = {
        "to": sender,
        "reply": reply,
        "timestamp": timestamp
    }

    return jsonify(response)

# For local testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
