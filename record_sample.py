import sounddevice as sd
from scipy.io.wavfile import write

fs = 44100  # Sample rate
seconds = 3  # Duration of recording

print("🎙️ Speak now for 3 seconds...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()

write("sample.wav", fs, recording)
print("✅ Saved to sample.wav")
