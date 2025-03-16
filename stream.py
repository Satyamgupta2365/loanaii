import os
import time
import requests
import streamlit as st
from gtts import gTTS
from groq import Groq
from PyPDF2 import PdfReader

# API Keys
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
SARVAM_API_KEY = "YOUR_SARVAM_API_KEY"

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Translation API details
TRANSLATE_URL = "https://api.sarvam.ai/translate"
TRANSLATE_HEADERS = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json"
}

def speak(text, lang="en"):
    """Converts text to speech and saves as an audio file."""
    tts = gTTS(text=text, lang=lang)
    tts.save("response.mp3")
    return "response.mp3"

def translate_text(text, source_lang, target_lang):
    """Translates text using Sarvam AI"""
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

def process_pdf(pdf_file, user_lang):
    """Reads a PDF file and processes it with Groq"""
    reader = PdfReader(pdf_file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    return full_text

def chatbot_response(user_input, user_lang):
    """Processes user input with Groq AI and translates the response."""
    messages = [{"role": "system", "content": "You are a helpful loan advisor."},
                {"role": "user", "content": user_input}]
    
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=1,
        max_completion_tokens=1024,
        top_p=1
    )
    
    response_text = completion.choices[0].message.content if completion.choices else "I didn't understand that."
    translated_response = translate_text(response_text, "en-IN", user_lang)
    return translated_response

# Streamlit UI
st.title("Loan Advisor Chatbot")
st.sidebar.header("Settings")
user_lang = st.sidebar.selectbox("Choose your language", ["en-IN", "hi-IN", "kn-IN", "ta-IN"])

uploaded_file = st.file_uploader("Upload a Loan-related PDF", type=["pdf"])
if uploaded_file:
    st.write("Processing your PDF...")
    pdf_text = process_pdf(uploaded_file, user_lang)
    st.text_area("Extracted Text", pdf_text, height=200)

user_input = st.text_input("Ask your loan-related question:")
if st.button("Get Advice"):
    if user_input:
        response = chatbot_response(user_input, user_lang)
        st.write("Loan Advisor:", response)
        audio_file = speak(response, lang=user_lang[:2])
        st.audio(audio_file, format="audio/mp3")
    else:
        st.warning("Please enter a question!")
