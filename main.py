from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# 🔑 Replace with your actual OpenAI API key
openai.api_key = "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"

@app.route('/sms', methods=['POST'])
def sms_reply():
    data = request.get_json()

    # Extract sender and message
    sender = data.get("sender", "")
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"to": sender, "reply": "❌ No message received."})

    try:
        # 🧠 Send message to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful SMS assistant. Reply briefly."},
                {"role": "user", "content": message}
            ],
            max_tokens=60,
            temperature=0.7
        )

        reply_text = response['choices'][0]['message']['content'].strip()

    except Exception as e:
        reply_text = f"⚠️ Error: {str(e)}"

    # Return response for SMS app
    return jsonify({
        "to": sender,
        "reply": reply_text
    })

@app.route('/')
def home():
    return "✅ SMS AI Bot is running."

if __name__ == '__main__':
    app.run(debug=True)
app.run(host="0.0.0.0", port=5000)

