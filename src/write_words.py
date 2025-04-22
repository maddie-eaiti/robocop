
from pynput import keyboard
from pynput.keyboard import Controller
import time



keyboard_controller = Controller()

if __name__ == "__main__":
    while True:
        keyboard_controller.type('Hello World!')
        keyboard_controller.press(keyboard.Key.enter)
        time.sleep(1)