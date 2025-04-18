import speech_recognition as sr

# Initialize recognizer
recognizer = sr.Recognizer()

# Use the default system microphone as the audio source
with sr.Microphone() as source:
    print("Say something...")
    # Adjust for ambient noise
    recognizer.adjust_for_ambient_noise(source)
    
    # Listen for the first phrase
    audio = recognizer.listen(source)

try:
    # Recognize speech using Google's API
    text = recognizer.recognize_google(audio)
    print(f"You said: {text}")

except sr.UnknownValueError:
    print("Sorry, could not understand audio.")
except sr.RequestError as e:
    print(f"Could not request results from Google Speech Recognition service; {e}")
