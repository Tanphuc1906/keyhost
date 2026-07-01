import threading
import time
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

class AutoBot:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.running = False
        self.thread = None

    def start_clicker(self, button_name, interval_ms, repeat_count):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._click_loop, args=(button_name, interval_ms, repeat_count))
        self.thread.start()

    def _click_loop(self, button_name, interval_ms, repeat_count):
        button = Button.left
        if button_name == 'Right':
            button = Button.right
        elif button_name == 'Middle':
            button = Button.middle

        interval = interval_ms / 1000.0
        count = 0
        while self.running and (repeat_count == 0 or count < repeat_count):
            self.mouse.click(button)
            count += 1
            if not self.running:
                break
            time.sleep(interval)
        self.running = False

    def start_key_presser(self, key_str, interval_ms, repeat_count):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._key_loop, args=(key_str, interval_ms, repeat_count))
        self.thread.start()

    def _key_loop(self, key_str, interval_ms, repeat_count):
        # Convert string to actual key if it's a special key like 'space', 'enter'
        key_to_press = key_str
        if hasattr(Key, key_str.lower()):
            key_to_press = getattr(Key, key_str.lower())
            
        interval = interval_ms / 1000.0
        count = 0
        while self.running and (repeat_count == 0 or count < repeat_count):
            try:
                self.keyboard.press(key_to_press)
                self.keyboard.release(key_to_press)
            except Exception:
                pass
            count += 1
            if not self.running:
                break
            time.sleep(interval)
        self.running = False

    def stop(self):
        self.running = False
