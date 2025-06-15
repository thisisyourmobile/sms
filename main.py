from flask import Flask, request, jsonify
import openai

openai.api_key = "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"

app = Flask(__name__)

@app.route('/', methods=['POST'])
def sms_reply():
    data = request.get_json()
    msg = data.get("message")
    sender = data.get("sender")

    if not msg:
        return jsonify({"to": sender, "reply": "Empty message."})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": msg}]
        )
        answer = response['choices'][0]['message']['content'].strip()
    except Exception as e:
        answer = "Error getting reply."

    return jsonify({
        "to": sender,
        "reply": answer
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
