from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# 🔑 Your OpenAI API Key
openai.api_key = "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"  # Replace with your real key

@app.route('/', methods=['GET'])
def sms_chatgpt():
    sender = request.args.get('sender')
    message = request.args.get('message')

    if not message:
        return jsonify({'reply': "No message received."})

    try:
        # 💬 ChatGPT call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Reply briefly in 1 SMS-friendly message."},
                {"role": "user", "content": message}
            ],
            max_tokens=60,  # keep short for SMS
            temperature=0.7
        )

        reply = response['choices'][0]['message']['content'].strip()
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

