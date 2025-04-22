import pyautogui
from pynput import keyboard
from pynput.keyboard import Controller
import speech_recognition as sr
import threading
import clippy
import time
from gemini import generate, help_transcribe
import json
from vocaliizer import speak

class DictationType:
    DICTATION = "dictation"
    COMMAND = "command"
    SMART_DICTATION = "smart dictation"

recognizer = sr.Recognizer()
mic = sr.Microphone()
transcribing = False
stop_event = threading.Event()
keyboard_controller = Controller()
highlight_context = None
dictation_type = DictationType.SMART_DICTATION
pressed_keys = set()
switch_mode = False
count_on_shift=0
stop_listening = None
audios = []

def recognize_speech(a) -> str:
    try:
        text = recognizer.recognize_google(a)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return ""

def background_job(stop_condition_func):
    global audios, stop_listening
    while stop_condition_func():
        print("Checking condition...")
        time.sleep(1)
    
    print("🔴 Stopped transcribing.")
    time.sleep(1)
    stop_listening(wait_for_stop=True)
    try:
        text = " ".join([recognize_speech(a) for a in audios])
    except sr.UnknownValueError:
        print("Could not understand audio")
    
    print(f"Final text: {text}")
    audios = []
    if not text:
        print("No text recognized.")
        return

    if dictation_type == DictationType.DICTATION:
        type_string(text)
    elif dictation_type == DictationType.COMMAND:
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
    elif dictation_type == DictationType.SMART_DICTATION:
        ss_path = "tmp/screenshot.png"
        take_screenshot(ss_path)
        time.sleep(0.1)
        response = help_transcribe(text, ss_path)
        print(f"Gemini transcription: {response}")
        type_string(response)
    

def get_transcribing_state():
    global transcribing
    return transcribing

def callback(recognizer, audio):
    print("Chunk recorded.")
    global stop_listening, highlight_context, dictation_type, audios
    print("🔵 Transcribing...")
    audios.append(audio)

def continuous_transcribe():
    global stop_listening, highlight_context, dictation_type

    stop_listening = recognizer.listen_in_background(mic, callback)
    

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
    global transcribing, highlight_context, pressed_keys, switch_mode, count_on_shift
    if key == keyboard.Key.shift:
        switch_mode = True
        count_on_shift = len(pressed_keys)
    else:
        switch_mode = False
    pressed_keys.add(key)
    # Check if the specific key to trigger transcription is pressed
    trigger_key = keyboard.Key.alt_l 
    if key == trigger_key:
        if not transcribing:
            print("🔒 Trigger key pressed — starting transcription...")
            transcribing = True
            highlight_context = get_highlight_context()
            stop_event.clear()
            threading.Thread(target=continuous_transcribe, daemon=True).start()
            threading.Thread(target=background_job, args=(get_transcribing_state,), daemon=True).start()
        return True
    # Allow other key presses to propagate normally
    return True


def on_release(key):
    global transcribing, pressed_keys, dictation_type, switch_mode, count_on_shift, stop_listening
    pressed_keys.discard(key)
    # Check if the key that stops transcription is released
    # Assuming releasing Left Option stops it, as before.
    if key == keyboard.Key.alt_l and transcribing:
        print("🔒 Trigger key released — stopping transcription...")
        transcribing = False
    
    if key == keyboard.Key.shift and switch_mode and len(pressed_keys) == count_on_shift:
        switch_mode = False
        if dictation_type == DictationType.DICTATION:
            speak("Switching to smart dictation mode.")
            dictation_type = DictationType.SMART_DICTATION
        elif dictation_type == DictationType.COMMAND:
            speak("Switching to dictation mode.")
            dictation_type = DictationType.DICTATION
        elif dictation_type == DictationType.SMART_DICTATION:
            speak("Switching to command mode.")
            dictation_type = DictationType.COMMAND
        print(f"Switching mode to {dictation_type}")



def setup():
    mic_list = sr.Microphone.list_microphone_names()
    print("Available microphones:")
    for index, name in enumerate(mic_list, start=1):
        print(f"Source {index}: {name}")
    input_index = int(input("Input source number: ")) - 1
    if input_index < 0 or input_index >= len(mic_list):
        print("❗ Invalid microphone index. Using default.")
        input_index = 0
    global mic
    mic = sr.Microphone(device_index=input_index)
    with mic as source:
        print("🔊 Adjusting for ambient noise...")
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
        clippy.clear_clipboard()
        time.sleep(0.05)  # Wait for clipboard to clear
        force_clipboard()
        time.sleep(0.05)  # Wait for clipboard to update
        return clippy.read_clipboard()
    except Exception as e:
        print(f"Error reading clipboard: {e}")
        return None


def force_clipboard():
    execute_shortcut([keyboard.Key.cmd, 'c'])

def take_screenshot(output_path="tmp/screenshot.png"):
    screenshot = pyautogui.screenshot()

    # Save to path
    screenshot.save(output_path)
    print(f"Screenshot saved to {output_path}")

setup()
# Start listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Press Option+d to begin transcribing speech... Release Left Option to stop. Press ESC to exit.")
listener.join()

