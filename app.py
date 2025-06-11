import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import escape
from werkzeug.exceptions import BadRequest
from sqlalchemy import Index
import requests
from langdetect import detect

# IndicTrans language codes
INDICTRANS_LANG_CODES = {
    'hi': 'hin_Deva', 'kn': 'kan_Knda', 'te': 'tel_Telu', 'ta': 'tam_Taml',
    'bn': 'ben_Beng', 'gu': 'guj_Gujr', 'ml': 'mal_Mlym', 'mr': 'mar_Deva',
    'pa': 'pan_Guru', 'or': 'ory_Orya', 'as': 'asm_Beng', 'en': 'eng_Latn'
}

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///feedback.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
app.config['DWANI_API_KEY'] = os.getenv('DWANI_API_KEY', 'your_email_dwani_krishnadevaraya')
app.config['DWANI_API_BASE_URL'] = os.getenv('DWANI_API_BASE_URL', 'https://dwani-krishnadevaraya.hf.space')

# Database setup
db = SQLAlchemy(app)

# Models
class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    text_translated = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(10), nullable=False, default='en')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_timestamp', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'text': self.text,
            'text_translated': self.text_translated,
            'category': self.category,
            'language': self.language,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

# Helpers
def translate_text(text, source_lang, target_lang='en'):
    try:
        api_key = app.config["DWANI_API_KEY"]
        headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
        src = INDICTRANS_LANG_CODES.get(source_lang, 'eng_Latn')
        tgt = INDICTRANS_LANG_CODES.get(target_lang, 'eng_Latn')

        response = requests.post(
            f"{app.config['DWANI_API_BASE_URL']}/v1/translate?api_key={api_key}",
            headers=headers,
            json={"sentences": [text], "src_lang": src, "tgt_lang": tgt},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("translations", [""])[0]
        else:
            app.logger.warning(f"DWANI API error: {response.status_code} - {response.text}")
            return text
    except Exception as e:
        app.logger.error(f"Translation exception: {str(e)}")
        return text

def validate_input(data, required_fields):
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise BadRequest(f"Missing required fields: {', '.join(missing)}")
    return {k: escape(v.strip()) if isinstance(v, str) else v for k, v in data.items()}

# Routes
@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Citizen Feedback API is running",
        "endpoints": {
            "submit_feedback": "/api/v1/feedback (POST)",
            "get_feedbacks": "/api/v1/feedbacks (GET)",
            "test_dwani_api": "/api/v1/test-dwani (GET)"
        }
    })

@app.route('/api/v1/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data received")

        data = validate_input(data, ['name', 'location', 'text', 'category'])

        source_lang = data.get('language') or detect(data['text'])

        SUPPORTED_LANGS = set(INDICTRANS_LANG_CODES.keys())
        if source_lang not in SUPPORTED_LANGS:
            source_lang = 'en'

        translated = None
        if source_lang != 'en':
            translated = translate_text(data['text'], source_lang)

        feedback = Feedback(
            name=data['name'],
            location=data['location'],
            text=data['text'],
            text_translated=translated,
            category=data['category'],
            language=source_lang
        )
        db.session.add(feedback)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Feedback submitted",
            "data": feedback.to_dict()
        }), 201

    except BadRequest as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Server error", "error": str(e)}), 500

@app.route('/api/v1/feedbacks', methods=['GET'])
def get_feedbacks():
    try:
        query = Feedback.query
        if request.args.get('search'):
            term = request.args['search']
            query = query.filter(
                Feedback.text.ilike(f'%{term}%') |
                Feedback.text_translated.ilike(f'%{term}%') |
                Feedback.name.ilike(f'%{term}%') |
                Feedback.category.ilike(f'%{term}%')
            )

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        translate = request.args.get('translate', 'false').lower() == 'true'

        feedbacks = query.order_by(Feedback.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        if translate:
            for fb in feedbacks.items:
                if not fb.text_translated and fb.language != 'en':
                    fb.text_translated = translate_text(fb.text, fb.language)
            db.session.commit()

        return jsonify({
            "status": "success",
            "count": feedbacks.total,
            "page": feedbacks.page,
            "pages": feedbacks.pages,
            "data": [fb.to_dict() for fb in feedbacks.items]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/test-dwani', methods=['GET'])
def test_dwani_api():
    try:
        headers = {'X-API-Key': app.config["DWANI_API_KEY"], 'Content-Type': 'application/json'}
        data = {"sentences": ["ನಮಸ್ಕಾರ, ನಾನು ಒಬ್ಬ ನಾಗರಿಕ"], "src_lang": "kan_Knda", "tgt_lang": "eng_Latn"}

        response = requests.post(
            f"{app.config['DWANI_API_BASE_URL']}/v1/translate?api_key={app.config['DWANI_API_KEY']}",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": "DWANI API is working",
                "data": response.json()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"DWANI API failed: {response.text}"
            }), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/test-translation', methods=['POST'])
def test_translation():
    try:
        data = request.get_json()
        if not data or not data.get('text'):
            raise BadRequest("Text is required")

        translated = translate_text(
            data['text'],
            data.get('source_language', 'en'),
            data.get('target_language', 'en')
        )

        return jsonify({
            "status": "success",
            "original_text": data['text'],
            "translated_text": translated
        })
    except BadRequest as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Initialize tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
