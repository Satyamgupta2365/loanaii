import os
import time
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
from PyPDF2 import PdfReader
from groq import Groq

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

# API Keys
GROQ_API_KEY = "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"
SARVAM_API_KEY = "9e95e478-07bd-4d90-ad75-7cbefa3d8172"

if not SARVAM_API_KEY:
    raise ValueError("Sarvam API key is missing!")

client = Groq(api_key=GROQ_API_KEY)

# Translation API details
TRANSLATE_URL = "https://api.sarvam.ai/translate"
TRANSLATE_HEADERS = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json"
}

# Convert text to speech and return the file path
def speak(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    audio_path = "static/response.mp3"
    tts.save(audio_path)
    return audio_path

# Translate text using Sarvam AI
def translate_text(text, source_lang, target_lang):
    payload = {
        "source_language_code": source_lang,
        "target_language_code": target_lang,
        "speaker_gender": "Male",
        "mode": "classic-colloquial",
        "model": "mayura:v1",
        "enable_preprocessing": False,
        "input": text
    }
    response = requests.post(TRANSLATE_URL, json=payload, headers=TRANSLATE_HEADERS)
    if response.status_code == 200:
        return response.json().get("translated_text", "Translation not available")
    return "Translation failed."

# Process chatbot response
def process_chatbot_response(user_input, user_lang):
    translated_input = translate_text(user_input, user_lang, "en-IN")
    
    messages = [
        {"role": "system", "content": "You are a helpful loan advisor."},
        {"role": "user", "content": translated_input}
    ]

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=1,
        max_completion_tokens=1024,
        top_p=1
    )

    response_text = completion.choices[0].message.content if completion.choices else "I couldn't understand."
    translated_response = translate_text(response_text, "en-IN", user_lang)

    audio_path = speak(translated_response, lang=user_lang[:2])
    return translated_response, audio_path

# Process PDF file
def process_pdf(file_path, user_lang):
    reader = PdfReader(file_path)
    text_data = []
    
    for page in reader.pages:
        page_text = page.extract_text()
        text_data.append(page_text)

    combined_text = "\n".join(text_data)
    translated_text = translate_text(combined_text, "en-IN", user_lang)

    audio_path = speak(translated_text, lang=user_lang[:2])
    return translated_text, audio_path

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    user_lang = request.json.get("language", "en-IN")
    
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    response_text, audio_path = process_chatbot_response(user_input, user_lang)
    return jsonify({"response": response_text, "audio": audio_path})

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_file = request.files["pdf"]
    user_lang = request.form.get("language", "en-IN")
    
    file_path = os.path.join("uploads", pdf_file.filename)
    pdf_file.save(file_path)

    translated_text, audio_path = process_pdf(file_path, user_lang)
    return jsonify({"response": translated_text, "audio": audio_path})

@app.route("/play-audio", methods=["GET"])
def play_audio():
    return send_file("static/response.mp3", mimetype="audio/mp3")

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
