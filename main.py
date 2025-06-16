from flask import Flask, request, jsonify
from openai import OpenAI  # Updated import

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key="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")  # Replace with your key

@app.route('/', methods=['GET'])
def sms_chatgpt():
    sender = request.args.get('sender')
    message = request.args.get('message')

    if not message:
        return jsonify({'reply': "No message received."})

    try:
        # Updated ChatGPT call (new API syntax)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Reply briefly in 1 SMS-friendly message."},
                {"role": "user", "content": message}
            ],
            max_tokens=60,
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
