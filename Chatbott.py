import openai  # OpenAI API
from flask import Flask, request, jsonify, render_template_string
import datetime
from transformers import pipeline
import os

app = Flask(__name__)
user_mood_history = {}

# Load Hugging Face emotion detection model
emotion_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

# Get OpenAI API Key securely
OPENAI_API_KEY = os.environ.get("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")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key is missing. Please set it as an environment variable named 'OPENAI_API_KEY'.")

openai.api_key = OPENAI_API_KEY  # Correct assignment

# Emotion analysis using Hugging Face model
def analyze_emotion(text):
    result = emotion_analyzer(text)[0]
    return result["label"]

# Track user emotions over time
def track_user_mood(user_id, mood):
    today = datetime.date.today().isoformat()
    if user_id not in user_mood_history:
        user_mood_history[user_id] = []
    user_mood_history[user_id].append({"date": today, "mood": mood})

    # Check if stress persists for 7 days
    stress_days = sum(1 for entry in user_mood_history[user_id] if entry["mood"] in ["sadness", "fear", "anger"])
    if stress_days >= 7:
        return "Emergency Alert! You've been experiencing negative emotions for a week. Consider seeking professional help."
    return None

# Get chatbot response using OpenAI API
def get_chatbot_response(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the latest model
            messages=[
                {"role": "system", "content": "You are a mental health assistant."},
                {"role": "user", "content": user_input},
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"  # Handle API errors gracefully

@app.route("/", methods=["GET"])
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mental Health Chatbot</title>
        </head>
        <body>
            <h1>Mental Health Chatbot</h1>
            <form action="/chat" method="post">
                <input type="text" name="message" placeholder="Ask a mental health question" required>
                <input type="submit" value="Send">
            </form>
        </body>
        </html>
    ''')

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form.get("message", "").strip()
    if not user_input:
        return jsonify({"error": "Message cannot be empty."}), 400

    user_id = "default_user"
    mood = analyze_emotion(user_input)
    emergency_message = track_user_mood(user_id, mood)
    chatbot_response = get_chatbot_response(user_input)

    response_text = chatbot_response
    if emergency_message:
        response_text += f"\n\n{emergency_message}"

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mental Health Chatbot</title>
        </head>
        <body>
            <h1>Mental Health Chatbot</h1>
            <form action="/chat" method="post">
                <input type="text" name="message" placeholder="Ask a mental health question" required>
                <input type="submit" value="Send">
            </form>
            <p><strong>Chatbot:</strong> {{ response }}</p>
        </body>
        </html>
    ''', response=response_text)

if __name__ == "__main__":
    app.run(debug=True)