from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# 🔑 Replace with your actual OpenAI API key
openai.api_key = "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"

@app.route("/", methods=["GET"])
def sms_to_ai():
    sender = request.args.get("sender")
    message = request.args.get("message")

    if not sender or not message:
        return jsonify({"reply": "❌ Missing sender or message."})

    try:
        # Get reply from ChatGPT
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        reply_text = chat.choices[0].message.content.strip()
    except Exception as e:
        reply_text = f"⚠️ Error: {e}"

    return jsonify({
        "to": sender,
        "reply": reply_text
    })

@app.route("/health", methods=["GET"])
def health_check():
    return "✅ Server is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
