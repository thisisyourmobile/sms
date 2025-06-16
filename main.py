from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 🔑 Gemini API Configuration (WARNING: Key is exposed)
GEMINI_API_KEY = "AIzaSyDhSgLirMhgWowniNLOeH1TMmaDDkswp80"  # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize model
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/sms', methods=['GET'])
def sms_reply():
    sender = request.args.get('sender', 'Unknown')
    message = request.args.get('message')
    
    if not message:
        return jsonify({'reply': "No message received."})

    try:
        # Gemini API call
        response = model.generate_content(
            f"Reply to this SMS in under 160 characters: {message}",
            generation_config={
                "max_output_tokens": 100,
                "temperature": 0.7
            }
        )
        
        reply = response.text.strip()[:160]
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'reply': "Error processing message"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
