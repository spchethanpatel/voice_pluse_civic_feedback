// scripts.js
let recognition;
const feedbackTextarea = document.getElementById('feedback');
const statusMsg = document.getElementById('status-msg');

function showStatusMessage(message, type = 'info') {
  statusMsg.textContent = message;
  statusMsg.className = `status-message ${type}`;
}

function startListening() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    showStatusMessage("Your browser does not support speech recognition.", 'error');
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    showStatusMessage("🎤 Listening... please speak.", 'info');
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    feedbackTextarea.value += (feedbackTextarea.value ? ' ' : '') + transcript;
    showStatusMessage("✅ Voice input added.", 'success');
  };

  recognition.onerror = (event) => {
    showStatusMessage("❌ Error: " + event.error, 'error');
  };

  recognition.onend = () => {
    showStatusMessage("🎙️ Voice input ended.", 'info');
  };

  recognition.start();
}

function closePopup() {
  document.getElementById('success-popup').classList.remove('visible');
}

document.getElementById('feedback-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const name = document.getElementById('name').value.trim();
  const location = document.getElementById('location').value.trim();
  const category = document.getElementById('category').value.trim();
  const feedback = feedbackTextarea.value.trim();

  if (!name || !location || !category || !feedback) {
    showStatusMessage("Please fill in all fields.", 'error');
    return;
  }

  try {
    const res = await fetch('http://localhost:5000/api/v1/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, location, text: feedback, category })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Submission failed');

    showStatusMessage("✅ Feedback submitted!", 'success');
    document.getElementById('success-popup').classList.add('visible');
    document.getElementById('feedback-form').reset();
  } catch (error) {
    showStatusMessage(`❌ ${error.message}`, 'error');
  }
});
