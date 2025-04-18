from gtts import gTTS
import os

def speak(text: str):
    tts = gTTS(text, lang="en")
    tts.save("tmp/output.mp3")
    # os.system("start output.mp3")  # Windows
    os.system("afplay tmp/output.mp3")  # macOS
    # os.system("mpg123 output.mp3")  # Linux
