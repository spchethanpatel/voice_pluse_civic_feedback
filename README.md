# 🗣️ Citizen Feedback Collector

A simple web application for collecting and managing public feedback from citizens on local issues such as sanitation, road maintenance, safety, and more.

## 🚀 Features

- 📋 Submit feedback via text or voice (speech recognition).
- 📍 Capture name, location, feedback text, and category.
- 🔒 Admin panel to view all feedback entries.
- 🧠 Built with Flask, SQLite, JavaScript, and modern CSS.

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript (SpeechRecognition API)
- **Backend**: Python Flask, Flask-SQLAlchemy
- **Database**: SQLite
- **Tools**: Flask-CORS

## 📂 Project Structure
voice_plus_civic_feedback/
│
├── server/                         # Flask backend
│   ├── app.py                      # Main Flask application
│   ├── routes.py                   # All route definitions
│   ├── models.py                   # SQLAlchemy models (e.g., Feedback)
│   ├── utils/
│   │   ├── speech_to_text.py       # Speech-to-text conversion logic
│   │   ├── translate_text.py       # Translation logic (native to English)
│   │   └── dwani_api.py            # API integration with authority
│   ├── templates/
│   │   └── index.html              # Web UI template
│   └── static/
│       ├── css/
│       ├── js/
│       │   └── recorder.js         # JS for voice recording & UI logic
│       └── images/
│
├── database/
│   └── feedback.db                 # SQLite DB (or initialization scripts)
│
├── tests/
│   ├── test_routes.py              # Unit tests for Flask routes
│   └── test_utils.py               # Tests for utility functions
│
├── run_project.py                 # Script to launch the app with browser
├── start_local.bat               # Windows batch file to run locally
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview
└── LICENSE                       # License file


## 📜 License

MIT License © 2025 S.P Chethan Patel

