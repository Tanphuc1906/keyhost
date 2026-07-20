import customtkinter as ctk
import threading
import json
import os
from autobot import AutoBot
from recorder import Recorder
from pynput import keyboard

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Auto Clicker & Key Presser (made by SDJ9)")
        self.geometry("500x550")
        
        self.autobot = AutoBot()
        self.recorder = Recorder()
        
        self.hotkey_str = "f8"
        self.record_hotkey_str = "f9"
        
        # UI Setup
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_clicker = self.tabview.add("Auto Clicker")
        self.tab_presser = self.tabview.add("Key Presser")
        self.tab_recorder = self.tabview.add("Record/Playback")
        self.tab_settings = self.tabview.add("Settings")
        
        self.setup_clicker_tab()
        self.setup_presser_tab()
        self.setup_recorder_tab()
        self.setup_settings_tab()
        
        self.load_config()
        
        self.status_label = ctk.CTkLabel(self, text="Status: Idle", text_color="green", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=10)
        
        # Start Global Listener
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.save_config()
        self.autobot.stop()
        self.recorder.stop_playback()
        self.recorder.stop_recording()
        if self.listener:
            self.listener.stop()
        self.destroy()

    def update_status(self, text, color="green"):
        self.status_label.configure(text=text, text_color=color)

    def on_press(self, key):
        try:
            key_name = key.char
        except AttributeError:
            key_name = key.name
            
        if key_name and key_name.lower() == self.hotkey_str.lower():
            # Run in main thread to avoid GUI thread issues
            self.after(0, self.toggle_action)
        elif key_name and key_name.lower() == self.record_hotkey_str.lower():
            self.after(0, self.toggle_recording)

    def toggle_action(self):
        current_tab = self.tabview.get()
        
        if self.autobot.running:
            self.autobot.stop()
            self.update_status("Status: Stopped", "red")
            return
            
        if self.recorder.is_playing:
            self.recorder.stop_playback()
            self.update_status("Status: Playback Stopped", "red")
            return
            
        if self.recorder.is_recording:
            self.toggle_recording()
            return

        # Nothing is running, so start based on current tab
        if current_tab == "Auto Clicker":
            self.start_clicker()
        elif current_tab == "Key Presser":
            self.start_presser()
        elif current_tab == "Record/Playback":
            self.start_playback()

    # --- Clicker Tab ---
    def setup_clicker_tab(self):
        self.btn_var = ctk.StringVar(value="Left")
        ctk.CTkLabel(self.tab_clicker, text="Mouse Button:").pack(pady=5)
        ctk.CTkOptionMenu(self.tab_clicker, variable=self.btn_var, values=["Left", "Right", "Middle"]).pack(pady=5)
        
        ctk.CTkLabel(self.tab_clicker, text="Interval:").pack(pady=5)
        
        self.click_interval_frame = ctk.CTkFrame(self.tab_clicker)
        self.click_interval_frame.pack(pady=5)
        
        ctk.CTkLabel(self.click_interval_frame, text="Hours").grid(row=0, column=0, padx=2)
        self.click_h = ctk.CTkEntry(self.click_interval_frame, width=40)
        self.click_h.insert(0, "0")
        self.click_h.grid(row=0, column=1, padx=2)
        
        ctk.CTkLabel(self.click_interval_frame, text="Mins").grid(row=0, column=2, padx=2)
        self.click_m = ctk.CTkEntry(self.click_interval_frame, width=40)
        self.click_m.insert(0, "0")
        self.click_m.grid(row=0, column=3, padx=2)
        
        ctk.CTkLabel(self.click_interval_frame, text="Secs").grid(row=0, column=4, padx=2)
        self.click_s = ctk.CTkEntry(self.click_interval_frame, width=40)
        self.click_s.insert(0, "0")
        self.click_s.grid(row=0, column=5, padx=2)
        
        ctk.CTkLabel(self.click_interval_frame, text="ms").grid(row=0, column=6, padx=2)
        self.click_ms = ctk.CTkEntry(self.click_interval_frame, width=50)
        self.click_ms.insert(0, "100")
        self.click_ms.grid(row=0, column=7, padx=2)
        
        ctk.CTkLabel(self.tab_clicker, text="Repeat (0 = Infinite):").pack(pady=5)
        self.click_repeat = ctk.CTkEntry(self.tab_clicker)
        self.click_repeat.insert(0, "0")
        self.click_repeat.pack(pady=5)
        
        self.btn_clicker_start = ctk.CTkButton(self.tab_clicker, text=f"Start (or {self.hotkey_str.upper()})", command=self.start_clicker)
        self.btn_clicker_start.pack(pady=15)

    def start_clicker(self):
        try:
            h = int(self.click_h.get())
            m = int(self.click_m.get())
            s = int(self.click_s.get())
            ms = int(self.click_ms.get())
            interval = h * 3600000 + m * 60000 + s * 1000 + ms
            repeat = int(self.click_repeat.get())
            btn = self.btn_var.get()
            self.autobot.start_clicker(btn, interval, repeat)
            self.update_status(f"Status: Auto Clicking ({btn})", "orange")
        except ValueError:
            self.update_status("Error: Invalid interval/repeat", "red")

    # --- Presser Tab ---
    def setup_presser_tab(self):
        ctk.CTkLabel(self.tab_presser, text="Key to press (e.g. 'a', 'enter', 'space'):").pack(pady=5)
        self.key_entry = ctk.CTkEntry(self.tab_presser)
        self.key_entry.insert(0, "a")
        self.key_entry.pack(pady=5)
        
        ctk.CTkLabel(self.tab_presser, text="Interval:").pack(pady=5)
        
        self.key_interval_frame = ctk.CTkFrame(self.tab_presser)
        self.key_interval_frame.pack(pady=5)
        
        ctk.CTkLabel(self.key_interval_frame, text="Hours").grid(row=0, column=0, padx=2)
        self.key_h = ctk.CTkEntry(self.key_interval_frame, width=40)
        self.key_h.insert(0, "0")
        self.key_h.grid(row=0, column=1, padx=2)
        
        ctk.CTkLabel(self.key_interval_frame, text="Mins").grid(row=0, column=2, padx=2)
        self.key_m = ctk.CTkEntry(self.key_interval_frame, width=40)
        self.key_m.insert(0, "0")
        self.key_m.grid(row=0, column=3, padx=2)
        
        ctk.CTkLabel(self.key_interval_frame, text="Secs").grid(row=0, column=4, padx=2)
        self.key_s = ctk.CTkEntry(self.key_interval_frame, width=40)
        self.key_s.insert(0, "0")
        self.key_s.grid(row=0, column=5, padx=2)
        
        ctk.CTkLabel(self.key_interval_frame, text="ms").grid(row=0, column=6, padx=2)
        self.key_ms = ctk.CTkEntry(self.key_interval_frame, width=50)
        self.key_ms.insert(0, "100")
        self.key_ms.grid(row=0, column=7, padx=2)
        
        ctk.CTkLabel(self.tab_presser, text="Repeat (0 = Infinite):").pack(pady=5)
        self.key_repeat = ctk.CTkEntry(self.tab_presser)
        self.key_repeat.insert(0, "0")
        self.key_repeat.pack(pady=5)
        
        self.btn_presser_start = ctk.CTkButton(self.tab_presser, text=f"Start (or {self.hotkey_str.upper()})", command=self.start_presser)
        self.btn_presser_start.pack(pady=15)

    def start_presser(self):
        try:
            h = int(self.key_h.get())
            m = int(self.key_m.get())
            s = int(self.key_s.get())
            ms = int(self.key_ms.get())
            interval = h * 3600000 + m * 60000 + s * 1000 + ms
            repeat = int(self.key_repeat.get())
            key_val = self.key_entry.get().strip()
            if not key_val:
                self.update_status("Error: Key cannot be empty", "red")
                return
            self.autobot.start_key_presser(key_val, interval, repeat)
            self.update_status(f"Status: Auto Pressing ({key_val})", "orange")
        except ValueError:
            self.update_status("Error: Invalid interval/repeat", "red")

    # --- Recorder Tab ---
    def setup_recorder_tab(self):
        self.record_btn = ctk.CTkButton(self.tab_recorder, text=f"Start Recording (or {self.record_hotkey_str.upper()})", command=self.toggle_recording, fg_color="red", hover_color="darkred")
        self.record_btn.pack(pady=10)
        
        ctk.CTkLabel(self.tab_recorder, text="Playback Repeat (0 = Infinite):").pack(pady=5)
        self.playback_repeat = ctk.CTkEntry(self.tab_recorder)
        self.playback_repeat.insert(0, "1")
        self.playback_repeat.pack(pady=5)
        
        self.play_btn = ctk.CTkButton(self.tab_recorder, text=f"Play (or {self.hotkey_str.upper()})", command=self.start_playback)
        self.play_btn.pack(pady=15)

    def toggle_recording(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            self.record_btn.configure(text=f"Start Recording (or {self.record_hotkey_str.upper()})", fg_color="red")
            # The stop hotkey was probably recorded, let's remove the last few press/release events that match our hotkey
            self._filter_hotkey_from_recording()
            self.update_status(f"Status: Recording Saved ({len(self.recorder.events)} events)", "green")
        else:
            self.recorder.start_recording()
            self.record_btn.configure(text=f"Stop Recording (or {self.record_hotkey_str.upper()})", fg_color="gray")
            self.update_status(f"Status: Recording... (Press {self.record_hotkey_str.upper()} to Stop)", "red")

    def _filter_hotkey_from_recording(self):
        # Remove the hotkey press/release events at the end of the recording
        events = self.recorder.events
        filtered = []
        for e in events:
            _, e_type, args = e
            if e_type in ('press', 'release'):
                key = args[0]
                try:
                    k_name = key.char
                except AttributeError:
                    k_name = key.name
                if k_name and (k_name.lower() == self.hotkey_str.lower() or k_name.lower() == self.record_hotkey_str.lower()):
                    continue # Skip our hotkey
            filtered.append(e)
        self.recorder.events = filtered

    def start_playback(self):
        try:
            repeat = int(self.playback_repeat.get())
            if not self.recorder.events:
                self.update_status("Status: No events recorded!", "red")
                return
            self.recorder.start_playback(repeat)
            self.update_status("Status: Playing back...", "orange")
        except ValueError:
            self.update_status("Error: Invalid repeat value", "red")

    # --- Settings Tab ---
    def setup_settings_tab(self):
        ctk.CTkLabel(self.tab_settings, text="Global Start/Stop Hotkey (e.g. 'f8', 'esc', 'a'):").pack(pady=5)
        self.hotkey_entry = ctk.CTkEntry(self.tab_settings)
        self.hotkey_entry.insert(0, self.hotkey_str)
        self.hotkey_entry.pack(pady=5)
        
        ctk.CTkLabel(self.tab_settings, text="Record Start/Stop Hotkey (e.g. 'f9'):").pack(pady=5)
        self.record_hotkey_entry = ctk.CTkEntry(self.tab_settings)
        self.record_hotkey_entry.insert(0, self.record_hotkey_str)
        self.record_hotkey_entry.pack(pady=5)
        
        ctk.CTkButton(self.tab_settings, text="Save Hotkeys", command=self.save_hotkeys).pack(pady=15)

    def save_hotkeys(self):
        new_hotkey = self.hotkey_entry.get().strip().lower()
        new_record_hotkey = self.record_hotkey_entry.get().strip().lower()
        if new_hotkey and new_record_hotkey:
            self.hotkey_str = new_hotkey
            self.record_hotkey_str = new_record_hotkey
            self.update_status(f"Status: Hotkeys updated", "green")
            hk_upper = self.hotkey_str.upper()
            rhk_upper = self.record_hotkey_str.upper()
            self.btn_clicker_start.configure(text=f"Start (or {hk_upper})")
            self.btn_presser_start.configure(text=f"Start (or {hk_upper})")
            self.play_btn.configure(text=f"Play (or {hk_upper})")
            
            if self.recorder.is_recording:
                self.record_btn.configure(text=f"Stop Recording (or {rhk_upper})")
            else:
                self.record_btn.configure(text=f"Start Recording (or {rhk_upper})")

    def save_config(self):
        config = {
            "btn_var": self.btn_var.get(),
            "click_h": self.click_h.get(),
            "click_m": self.click_m.get(),
            "click_s": self.click_s.get(),
            "click_ms": self.click_ms.get(),
            "click_repeat": self.click_repeat.get(),
            
            "key_entry": self.key_entry.get(),
            "key_h": self.key_h.get(),
            "key_m": self.key_m.get(),
            "key_s": self.key_s.get(),
            "key_ms": self.key_ms.get(),
            "key_repeat": self.key_repeat.get(),
            
            "playback_repeat": self.playback_repeat.get(),
            
            "hotkey_str": self.hotkey_str,
            "record_hotkey_str": self.record_hotkey_str
        }
        try:
            with open("config.json", "w") as f:
                json.dump(config, f)
        except Exception as e:
            print("Error saving config:", e)

    def load_config(self):
        if not os.path.exists("config.json"):
            return
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                
            if "btn_var" in config: self.btn_var.set(config["btn_var"])
            
            self._set_entry(self.click_h, config.get("click_h", "0"))
            self._set_entry(self.click_m, config.get("click_m", "0"))
            self._set_entry(self.click_s, config.get("click_s", "0"))
            self._set_entry(self.click_ms, config.get("click_ms", "100"))
            self._set_entry(self.click_repeat, config.get("click_repeat", "0"))
            
            self._set_entry(self.key_entry, config.get("key_entry", "a"))
            self._set_entry(self.key_h, config.get("key_h", "0"))
            self._set_entry(self.key_m, config.get("key_m", "0"))
            self._set_entry(self.key_s, config.get("key_s", "0"))
            self._set_entry(self.key_ms, config.get("key_ms", "100"))
            self._set_entry(self.key_repeat, config.get("key_repeat", "0"))
            
            self._set_entry(self.playback_repeat, config.get("playback_repeat", "1"))
            
            if "hotkey_str" in config: self.hotkey_str = config["hotkey_str"]
            if "record_hotkey_str" in config: self.record_hotkey_str = config["record_hotkey_str"]
            
            self._set_entry(self.hotkey_entry, self.hotkey_str)
            self._set_entry(self.record_hotkey_entry, self.record_hotkey_str)
            
            hk_upper = self.hotkey_str.upper()
            rhk_upper = self.record_hotkey_str.upper()
            self.btn_clicker_start.configure(text=f"Start (or {hk_upper})")
            self.btn_presser_start.configure(text=f"Start (or {hk_upper})")
            self.play_btn.configure(text=f"Play (or {hk_upper})")
            self.record_btn.configure(text=f"Start Recording (or {rhk_upper})")
            
        except Exception as e:
            print("Error loading config:", e)
            
    def _set_entry(self, entry, value):
        entry.delete(0, 'end')
        entry.insert(0, str(value))

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
