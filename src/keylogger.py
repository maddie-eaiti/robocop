from pynput import keyboard
from pynput.keyboard import Controller
import speech_recognition as sr
import threading
import clippy
import time
from gemini import generate
import json

recognizer = sr.Recognizer()
mic = sr.Microphone()
transcribing = False
stop_event = threading.Event()
keyboard_controller = Controller()
highlight_context = None
dictation_type = "command"


def continuous_transcribe():
    audios = []
    with mic as source:
        while not stop_event.is_set():
            try:
                print("🎤 Listening...")
                audios.append(recognizer.listen(source, timeout=10, phrase_time_limit=60))
            except sr.WaitTimeoutError:
                print("⏳ No speech detected...")
            except sr.UnknownValueError:
                print("❗ Couldn't understand.")
            except sr.RequestError as e:
                print(f"❗ API error: {e}")
                break
    
    if audios:
        texts = []
        try:
            print("📝 Transcribing...")
            for audio in audios:
                texts.append(recognizer.recognize_google(audio))
        except sr.UnknownValueError:
            print("❗ Couldn't understand.")
        except sr.RequestError as e:
            print(f"❗ API error: {e}")
        text = ' '.join(texts)
        print(f"You said: {text}")
        print(f"Current highlight context: {highlight_context}")
        if dictation_type == "dictation":
            type_string(text)
        if dictation_type == "command":
            response = generate(highlight_context, '', text)
            if response:
                response_obj = json.loads(response[7:-4])
                if "oldText" in response_obj:
                    old_text = response_obj["oldText"]
                    new_text = response_obj["newText"]
                    print(f"Old text: {old_text}")
                    print(f"New text: {new_text}")
                    if old_text != highlight_context:
                        keyboard_controller.press(keyboard.Key.right)
                        for i in range(len(old_text)):
                            keyboard_controller.press(keyboard.Key.backspace)
                    type_string(new_text)

    print("🔴 Stopped transcribing.")


def type_string(input_string):
    """
    Simulates typing a string by converting it into keyboard inputs.

    Args:
        input_string (str): The string to type.
    """
    text = process_shortcuts(input_string)
    for char in text:
        keyboard_controller.type(char)
    print(f"Typed: {input_string}")


def on_press(key):
    global transcribing, highlight_context
    # Check if the specific key to trigger transcription is pressed
    trigger_key = keyboard.Key.alt_l 
    if key == trigger_key:
        if not transcribing:
            print("🔒 Trigger key pressed — starting transcription...")
            transcribing = True
            highlight_context = get_highlight_context()
            stop_event.clear()
            threading.Thread(target=continuous_transcribe, daemon=True).start()
        return True  # Stop propagation

    # Allow other key presses to propagate normally
    return True


def on_release(key):
    global transcribing
    # Check if the key that stops transcription is released
    # Assuming releasing Left Option stops it, as before.
    if key == keyboard.Key.alt_l:
        if transcribing:
            print("🔓 Option key released — stopping transcription...")
            transcribing = False
            stop_event.set()


def setup():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🟢 Ready to transcribe...")


def process_shortcuts(transcript: str) -> list[keyboard.Key]:
    transcript_pieces = transcript.split("insert footnote")
    for piece in transcript_pieces:
        if "new line" in piece:
            piece = piece.replace("new line", "")
            execute_shortcut([keyboard.Key.enter])
    new_transcript = transcript
    if "insert footnote" in new_transcript.lower():
        execute_shortcut([keyboard.Key.cmd, keyboard.Key.alt_r, 'f'])
        new_transcript = new_transcript.replace("insert footnote", "")
    if "new line" in new_transcript.lower():
        execute_shortcut([keyboard.Key.enter])
        new_transcript = new_transcript.replace("new line", "")
    return new_transcript


def execute_shortcut(sequence: list[keyboard.Key]):
    for key in sequence:
        keyboard_controller.press(key)
    for key in reversed(sequence):
        keyboard_controller.release(key)


def get_highlight_context():
    """
    Returns the current highlight_context of the clipboard.
    """
    try:
        force_clipboard()
        time.sleep(0.1)  # Wait for clipboard to update
        return clippy.read_clipboard()
    except Exception as e:
        print(f"Error reading clipboard: {e}")
        return None


def force_clipboard():
    execute_shortcut([keyboard.Key.cmd, 'c'])


setup()
# Start listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Press Option+d to begin transcribing speech... Release Left Option to stop. Press ESC to exit.")
listener.join()
