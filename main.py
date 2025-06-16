from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# 🔥 UNSECURED - Key is hardcoded (DANGEROUS!)
DEEPSEEK_API_KEY = "sk-9efc6cf0f33349ac9d747c267c74d62b"  # ← REPLACE (and never share this file!)
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

@app.route('/sms', methods=['GET'])
def sms_reply():
    message = request.args.get('message', '')
    if not message:
        return jsonify({'reply': "No message received."})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Reply in 1 SMS (160 chars max)."},
                {"role": "user", "content": message}
            ],
            max_tokens=100
        )
        reply = response.choices[0].message.content.strip()[:160]
        return jsonify({'reply': reply})
    
    except Exception as e:
        return jsonify({'reply': "Error processing message."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Local use only!
