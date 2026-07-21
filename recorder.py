import time
import threading
import json
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController

def _serialize_key(key):
    if isinstance(key, keyboard.Key):
        return {"type": "Key", "name": key.name}
    elif isinstance(key, keyboard.KeyCode):
        return {"type": "KeyCode", "char": key.char, "vk": key.vk}
    else:
        return {"type": "unknown", "repr": str(key)}

def _deserialize_key(data):
    if data.get("type") == "Key":
        return getattr(keyboard.Key, data["name"], None)
    elif data.get("type") == "KeyCode":
        return keyboard.KeyCode(vk=data.get("vk"), char=data.get("char"))
    return None

class Recorder:
    def __init__(self):
        self.events = []
        self.is_recording = False
        self.is_playing = False
        
        self.mouse_listener = None
        self.keyboard_listener = None
        self.start_time = 0
        
        self.mouse_ctrl = MouseController()
        self.keyboard_ctrl = KeyboardController()
        self.play_thread = None
        
    def _add_event(self, event_type, *args):
        if not self.is_recording:
            return
        current_time = time.time() - self.start_time
        self.events.append((current_time, event_type, args))

    def on_move(self, x, y):
        self._add_event('move', x, y)

    def on_click(self, x, y, button, pressed):
        self._add_event('click', x, y, button.name, pressed)

    def on_scroll(self, x, y, dx, dy):
        self._add_event('scroll', x, y, dx, dy)

    def on_press(self, key):
        self._add_event('press', key)

    def on_release(self, key):
        self._add_event('release', key)

    def start_recording(self):
        self.events = []
        self.is_recording = True
        self.start_time = time.time()
        
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll)
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
            
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_recording(self):
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.mouse_listener = None
        self.keyboard_listener = None
            
    def start_playback(self, repeat_count=1):
        if not self.events or self.is_playing:
            return
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_loop, args=(repeat_count,), daemon=True)
        self.play_thread.start()
        
    def _play_loop(self, repeat_count):
        count = 0
        while self.is_playing and (repeat_count == 0 or count < repeat_count):
            start_play_time = time.time()
            for event in self.events:
                if not self.is_playing:
                    break
                event_time, event_type, args = event
                target_time = start_play_time + event_time
                current_time = time.time()
                
                if target_time > current_time:
                    time.sleep(target_time - current_time)
                
                if event_type == 'move':
                    self.mouse_ctrl.position = (args[0], args[1])
                elif event_type == 'click':
                    x, y, btn_name, pressed = args
                    btn = getattr(mouse.Button, btn_name, mouse.Button.left)
                    self.mouse_ctrl.position = (x, y)
                    if pressed:
                        self.mouse_ctrl.press(btn)
                    else:
                        self.mouse_ctrl.release(btn)
                elif event_type == 'scroll':
                    self.mouse_ctrl.scroll(args[2], args[3])
                elif event_type == 'press':
                    try:
                        self.keyboard_ctrl.press(args[0])
                    except Exception:
                        pass
                elif event_type == 'release':
                    try:
                        self.keyboard_ctrl.release(args[0])
                    except Exception:
                        pass
                        
            count += 1
        self.is_playing = False

    def stop_playback(self):
        self.is_playing = False

    def save_to_file(self, filename):
        data = []
        for event_time, event_type, args in self.events:
            if event_type in ('press', 'release'):
                s_args = [_serialize_key(args[0])]
            else:
                s_args = list(args)
            data.append({"time": event_time, "type": event_type, "args": s_args})
        with open(filename, 'w') as f:
            json.dump(data, f)

    def load_from_file(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        self.events = []
        for item in data:
            event_time = item["time"]
            event_type = item["type"]
            args = item["args"]
            if event_type in ('press', 'release'):
                d_key = _deserialize_key(args[0])
                self.events.append((event_time, event_type, (d_key,)))
            else:
                self.events.append((event_time, event_type, tuple(args)))
