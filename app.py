from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from textblob import TextBlob
import sqlite3
import os
import io
import csv
from pydub import AudioSegment
import requests

app = Flask(__name__)

# 🔐 DWANI API configuration
email_id = "mohammedsabeel063@gmail.com"
DWANI_API_KEY = email_id + "_dwani"
DWANI_API_BASE_URL = "https://dwani-dwani-api.hf.space"

# 🛠 Initialize database
def init_db():
    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        sentiment TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# 🏠 Dashboard route
@app.route('/')
def dashboard():
    conn = sqlite3.connect('feedback.db')
    feedbacks = conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("dashboard.html", feedbacks=feedbacks)

# 🔊 Audio transcription using DWANI API
def transcribe_with_dwani(audio_bytes):
    try:
        print("📡 Sending audio to DWANI API...")
        headers = {"Authorization": f"Bearer {DWANI_API_KEY}"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}

        response = requests.post(
            f"{DWANI_API_BASE_URL}/predict",
            headers=headers,
            files=files
        )

        print("🔁 DWANI Response Status:", response.status_code)

        if response.status_code == 200:
            return response.json().get("text", "").strip()
        else:
            print("❌ DWANI API Error:", response.text)
            return None
    except Exception as e:
        print("❌ DWANI API Exception:", str(e))
        return None

# 🎙️ Voice recording and analysis
@app.route('/record', methods=['POST'])
def record():
    try:
        print("🎧 Received audio from user...")

        audio_file = request.files['audio_data']
        raw_data = audio_file.read()

        # Convert WebM to WAV
        audio = AudioSegment.from_file(io.BytesIO(raw_data), format="webm")
        wav_path = "temp.wav"
        audio.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            wav_bytes = audio_data.get_wav_data()

        # Try DWANI API
        text = transcribe_with_dwani(wav_bytes)

        # Fallback to Google if DWANI fails
        if not text:
            print("⏪ Falling back to Google Speech Recognition...")
            try:
                text = recognizer.recognize_google(audio_data)
                print("✅ Google Transcription:", text)
            except sr.UnknownValueError:
                return jsonify({"success": False, "message": "Could not understand audio."})
            except sr.RequestError:
                return jsonify({"success": False, "message": "Google Speech Recognition failed."})

        # 🔍 Sentiment analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.2:
            sentiment = "Positive"
        elif polarity < -0.2:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        print("📊 Polarity:", polarity)
        print("🔍 Sentiment:", sentiment)

        # 💾 Save to SQLite
        conn = sqlite3.connect('feedback.db')
        conn.execute("INSERT INTO feedback (text, sentiment) VALUES (?, ?)", (text, sentiment))
        conn.commit()
        conn.close()

        # 🧾 Save to CSV
        with open("feedback_log.csv", "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([text, sentiment])

        os.remove(wav_path)

        return jsonify({"success": True, "text": text, "sentiment": sentiment})

    except Exception as e:
        print("🔥 Error:", str(e))
        return jsonify({"success": False, "message": str(e)})

# 🏁 Start the app
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
