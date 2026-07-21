import customtkinter as ctk
import threading
import json
import os
import sys
from tkinter import filedialog
from PIL import Image
from autobot import AutoBot
from recorder import Recorder
from pynput import keyboard

# --- CYBERPUNK / ANIME TECH THEME COLORS ---
BG_COLOR = "#0b0f19"         # Deep Dark Blue
FRAME_COLOR = "#151c2f"      # Lighter Dark Blue
ACCENT_CYAN = "#00f0ff"      # Neon Cyan
ACCENT_PINK = "#ff0055"      # Neon Pink
ACCENT_PURPLE = "#b026ff"    # Neon Purple
TEXT_COLOR = "#e0e6ed"       # Soft White
FONT_MAIN = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_BIG = ("Segoe UI", 20, "bold")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OverlayNotification(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        self.config(bg=BG_COLOR)
        
        self.label = ctk.CTkLabel(
            self, text="", font=FONT_BOLD, text_color=ACCENT_CYAN, 
            corner_radius=8, fg_color=FRAME_COLOR, padx=15, pady=15
        )
        self.label.pack(fill="both", expand=True, padx=2, pady=2)
        self.withdraw()

    def show_msg(self, title, stop_hk, exit_hk):
        msg = f"⚡ {title} IS RUNNING\n[ {stop_hk} ] to STOP\n[ {exit_hk} ] to EXIT APP"
        self.label.configure(text=msg)
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - width - 20
        y = screen_height - height - 60
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()

    def hide_msg(self):
        self.withdraw()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Auto Clicker Pro - Cyber Anime Edition (by SDJ9)")
        self.geometry("600x700")
        self.configure(fg_color=BG_COLOR)
        
        self.autobot = AutoBot()
        self.recorder = Recorder()
        
        self.hotkey_str = "f8"
        self.record_hotkey_str = "f9"
        self.exit_hotkey_str = "f10"
        self.overlay = OverlayNotification(self)
        
        # UI Setup
        # Title Header
        self.header_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.header_frame.pack(fill="x", pady=(15, 0))
        
        inner_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        inner_frame.pack(anchor="center")
        
        try:
            img_path = resource_path("logo.png")
            logo_img = ctk.CTkImage(light_image=Image.open(img_path), dark_image=Image.open(img_path), size=(50, 50))
            self.logo_label = ctk.CTkLabel(inner_frame, image=logo_img, text="")
            self.logo_label.pack(side="left", padx=(0, 10))
        except Exception:
            pass
            
        text_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        text_frame.pack(side="left")
        
        self.title_lbl = ctk.CTkLabel(text_frame, text="AUTOMATE STUDIO (オートメーションスタジオ)", font=FONT_BIG, text_color=ACCENT_CYAN)
        self.title_lbl.pack(anchor="w")
        
        self.subtitle_lbl = ctk.CTkLabel(text_frame, text="made by SDJ9", font=FONT_MAIN, text_color=ACCENT_PURPLE)
        self.subtitle_lbl.pack(anchor="w")

        # Custom TabView Styling
        self.tabview = ctk.CTkTabview(
            self, fg_color=FRAME_COLOR, 
            segmented_button_fg_color=BG_COLOR,
            segmented_button_selected_color=ACCENT_PURPLE,
            segmented_button_selected_hover_color=ACCENT_CYAN,
            segmented_button_unselected_hover_color="#2a3556",
            text_color=TEXT_COLOR
        )
        self.tabview.pack(padx=20, pady=15, fill="both", expand=True)
        
        self.tab_clicker = self.tabview.add("Auto Clicker")
        self.tab_presser = self.tabview.add("Key Presser")
        self.tab_recorder = self.tabview.add("Record/Playback")
        self.tab_settings = self.tabview.add("Settings")
        
        self.setup_clicker_tab()
        self.setup_presser_tab()
        self.setup_recorder_tab()
        self.setup_settings_tab()
        
        self.load_config()
        
        self.status_frame = ctk.CTkFrame(self, fg_color=FRAME_COLOR, height=40, corner_radius=10)
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.status_label = ctk.CTkLabel(self.status_frame, text="SYSTEM IDLE", text_color=ACCENT_CYAN, font=FONT_BOLD)
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

    def update_status(self, text, color=ACCENT_CYAN):
        self.status_label.configure(text=text.upper(), text_color=color)

    def on_press(self, key):
        try:
            key_name = key.char
        except AttributeError:
            key_name = key.name
            
        if key_name and key_name.lower() == self.hotkey_str.lower():
            self.after(0, self.toggle_action)
        elif key_name and key_name.lower() == self.record_hotkey_str.lower():
            self.after(0, self.toggle_recording)
        elif key_name and key_name.lower() == self.exit_hotkey_str.lower():
            self.after(0, self.on_closing)

    def toggle_action(self):
        current_tab = self.tabview.get()
        
        if self.autobot.running:
            self.autobot.stop()
            self.update_status("SYSTEM STOPPED", ACCENT_PINK)
            self.overlay.hide_msg()
            return
            
        if self.recorder.is_playing:
            self.recorder.stop_playback()
            self.update_status("PLAYBACK STOPPED", ACCENT_PINK)
            self.overlay.hide_msg()
            return
            
        if self.recorder.is_recording:
            self.toggle_recording()
            return

        if current_tab == "Auto Clicker":
            self.start_clicker()
        elif current_tab == "Key Presser":
            self.start_presser()
        elif current_tab == "Record/Playback":
            self.start_playback()

    def create_card(self, parent, title):
        frame = ctk.CTkFrame(parent, fg_color=BG_COLOR, corner_radius=10)
        frame.pack(fill="x", pady=10, padx=10)
        lbl = ctk.CTkLabel(frame, text=title, font=FONT_TITLE, text_color=ACCENT_CYAN)
        lbl.pack(anchor="w", padx=15, pady=(10, 5))
        return frame

    # --- Clicker Tab ---
    def setup_clicker_tab(self):
        card1 = self.create_card(self.tab_clicker, "TARGET")
        self.btn_var = ctk.StringVar(value="Left")
        
        row1 = ctk.CTkFrame(card1, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(row1, text="Mouse Button:", font=FONT_BOLD).pack(side="left")
        ctk.CTkOptionMenu(
            row1, variable=self.btn_var, values=["Left", "Right", "Middle"], 
            fg_color=FRAME_COLOR, button_color=ACCENT_PURPLE, button_hover_color=ACCENT_CYAN
        ).pack(side="right")
        
        card2 = self.create_card(self.tab_clicker, "TIMING & REPEAT")
        
        interval_grid = ctk.CTkFrame(card2, fg_color="transparent")
        interval_grid.pack(pady=10)
        
        labels = ["Hours", "Mins", "Secs", "ms"]
        entries = []
        for i, text in enumerate(labels):
            ctk.CTkLabel(interval_grid, text=text, font=FONT_MAIN).grid(row=0, column=i*2, padx=(10,2))
            entry = ctk.CTkEntry(interval_grid, width=50, fg_color=FRAME_COLOR, border_color=ACCENT_CYAN)
            entry.insert(0, "0" if text != "ms" else "100")
            entry.grid(row=0, column=i*2+1, padx=2)
            entries.append(entry)
        
        self.click_h, self.click_m, self.click_s, self.click_ms = entries
        
        rep_row = ctk.CTkFrame(card2, fg_color="transparent")
        rep_row.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(rep_row, text="Repeat (0 = Infinite):", font=FONT_BOLD).pack(side="left")
        self.click_repeat = ctk.CTkEntry(rep_row, width=80, fg_color=FRAME_COLOR, border_color=ACCENT_PURPLE)
        self.click_repeat.insert(0, "0")
        self.click_repeat.pack(side="right")
        
        self.btn_clicker_start = ctk.CTkButton(
            self.tab_clicker, text=f"START ACTION [ {self.hotkey_str.upper()} ]", 
            command=self.start_clicker, font=FONT_TITLE, fg_color=ACCENT_CYAN, 
            text_color=BG_COLOR, hover_color=ACCENT_PURPLE, height=45, corner_radius=8
        )
        self.btn_clicker_start.pack(pady=20, fill="x", padx=30)

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
            self.update_status(f"CLICKING >> {btn.upper()}", ACCENT_CYAN)
            self.overlay.show_msg("AUTO CLICKER", self.hotkey_str.upper(), self.exit_hotkey_str.upper())
        except ValueError:
            self.update_status("ERROR: INVALID INPUT", ACCENT_PINK)

    # --- Presser Tab ---
    def setup_presser_tab(self):
        card1 = self.create_card(self.tab_presser, "TARGET KEY")
        
        row1 = ctk.CTkFrame(card1, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(row1, text="Key to press (e.g. 'a', 'space'):", font=FONT_BOLD).pack(side="left")
        self.key_entry = ctk.CTkEntry(row1, width=120, fg_color=FRAME_COLOR, border_color=ACCENT_CYAN)
        self.key_entry.insert(0, "a")
        self.key_entry.pack(side="right")
        
        card2 = self.create_card(self.tab_presser, "TIMING & REPEAT")
        interval_grid = ctk.CTkFrame(card2, fg_color="transparent")
        interval_grid.pack(pady=10)
        
        labels = ["Hours", "Mins", "Secs", "ms"]
        entries = []
        for i, text in enumerate(labels):
            ctk.CTkLabel(interval_grid, text=text, font=FONT_MAIN).grid(row=0, column=i*2, padx=(10,2))
            entry = ctk.CTkEntry(interval_grid, width=50, fg_color=FRAME_COLOR, border_color=ACCENT_CYAN)
            entry.insert(0, "0" if text != "ms" else "100")
            entry.grid(row=0, column=i*2+1, padx=2)
            entries.append(entry)
            
        self.key_h, self.key_m, self.key_s, self.key_ms = entries
        
        rep_row = ctk.CTkFrame(card2, fg_color="transparent")
        rep_row.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(rep_row, text="Repeat (0 = Infinite):", font=FONT_BOLD).pack(side="left")
        self.key_repeat = ctk.CTkEntry(rep_row, width=80, fg_color=FRAME_COLOR, border_color=ACCENT_PURPLE)
        self.key_repeat.insert(0, "0")
        self.key_repeat.pack(side="right")
        
        self.btn_presser_start = ctk.CTkButton(
            self.tab_presser, text=f"START ACTION [ {self.hotkey_str.upper()} ]", 
            command=self.start_presser, font=FONT_TITLE, fg_color=ACCENT_CYAN, 
            text_color=BG_COLOR, hover_color=ACCENT_PURPLE, height=45, corner_radius=8
        )
        self.btn_presser_start.pack(pady=20, fill="x", padx=30)

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
                self.update_status("ERROR: KEY CANNOT BE EMPTY", ACCENT_PINK)
                return
            self.autobot.start_key_presser(key_val, interval, repeat)
            self.update_status(f"PRESSING >> {key_val.upper()}", ACCENT_CYAN)
            self.overlay.show_msg("KEY PRESSER", self.hotkey_str.upper(), self.exit_hotkey_str.upper())
        except ValueError:
            self.update_status("ERROR: INVALID INPUT", ACCENT_PINK)

    # --- Recorder Tab ---
    def setup_recorder_tab(self):
        card1 = self.create_card(self.tab_recorder, "RECORD MODULE")
        
        self.record_btn = ctk.CTkButton(
            card1, text=f"START REC [ {self.record_hotkey_str.upper()} ]", 
            command=self.toggle_recording, font=FONT_TITLE, fg_color=ACCENT_PINK, 
            hover_color="#c9003b", text_color="white", height=45
        )
        self.record_btn.pack(pady=(5, 15), padx=20, fill="x")
        
        io_row = ctk.CTkFrame(card1, fg_color="transparent")
        io_row.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkButton(io_row, text="SAVE RECORDING", command=self.save_recording, fg_color=FRAME_COLOR, border_width=1, border_color=ACCENT_CYAN, text_color=ACCENT_CYAN, hover_color=ACCENT_PURPLE).pack(side="left", expand=True, padx=(0,5))
        ctk.CTkButton(io_row, text="LOAD RECORDING", command=self.load_recording, fg_color=FRAME_COLOR, border_width=1, border_color=ACCENT_PINK, text_color=ACCENT_PINK, hover_color=ACCENT_PURPLE).pack(side="right", expand=True, padx=(5,0))

        card2 = self.create_card(self.tab_recorder, "PLAYBACK MODULE")
        
        rep_row = ctk.CTkFrame(card2, fg_color="transparent")
        rep_row.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(rep_row, text="Playback Repeat (0 = Infinite):", font=FONT_BOLD).pack(side="left")
        self.playback_repeat = ctk.CTkEntry(rep_row, width=80, fg_color=FRAME_COLOR, border_color=ACCENT_CYAN)
        self.playback_repeat.insert(0, "1")
        self.playback_repeat.pack(side="right")
        
        self.play_btn = ctk.CTkButton(
            card2, text=f"PLAY SEQUENCE [ {self.hotkey_str.upper()} ]", 
            command=self.start_playback, font=FONT_TITLE, fg_color=ACCENT_CYAN, 
            hover_color=ACCENT_PURPLE, text_color=BG_COLOR, height=45
        )
        self.play_btn.pack(pady=(5, 15), padx=20, fill="x")

    def save_recording(self):
        if not self.recorder.events:
            self.update_status("ERROR: NO DATA TO SAVE", ACCENT_PINK)
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            try:
                self.recorder.save_to_file(filepath)
                self.update_status("RECORDING SAVED", ACCENT_CYAN)
            except Exception as e:
                self.update_status("ERROR SAVING", ACCENT_PINK)

    def load_recording(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filepath:
            try:
                self.recorder.load_from_file(filepath)
                self.update_status(f"LOADED {len(self.recorder.events)} EVENTS", ACCENT_CYAN)
            except Exception as e:
                self.update_status("ERROR LOADING", ACCENT_PINK)

    def toggle_recording(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            self.record_btn.configure(text=f"START REC [ {self.record_hotkey_str.upper()} ]", fg_color=ACCENT_PINK)
            self.overlay.hide_msg()
            self._filter_hotkey_from_recording()
            self.update_status(f"DATA SAVED: {len(self.recorder.events)} EVENTS", ACCENT_CYAN)
        else:
            self.recorder.start_recording()
            self.record_btn.configure(text=f"STOP REC [ {self.record_hotkey_str.upper()} ]", fg_color="#555555")
            self.update_status(f"RECORDING >> ACTIVE", ACCENT_PINK)
            self.overlay.show_msg("RECORDER", self.record_hotkey_str.upper(), self.exit_hotkey_str.upper())

    def _filter_hotkey_from_recording(self):
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
                    continue
            filtered.append(e)
        self.recorder.events = filtered

    def start_playback(self):
        try:
            repeat = int(self.playback_repeat.get())
            if not self.recorder.events:
                self.update_status("ERROR: MEMORY EMPTY", ACCENT_PINK)
                return
            self.recorder.start_playback(repeat)
            self.update_status("PLAYBACK >> ACTIVE", ACCENT_CYAN)
            self.overlay.show_msg("PLAYBACK", self.hotkey_str.upper(), self.exit_hotkey_str.upper())
        except ValueError:
            self.update_status("ERROR: INVALID REPEAT", ACCENT_PINK)

    # --- Settings Tab ---
    def setup_settings_tab(self):
        card = self.create_card(self.tab_settings, "SYSTEM KEYBINDS")
        
        def add_setting_row(parent, label_text, default_val):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=8)
            ctk.CTkLabel(row, text=label_text, font=FONT_BOLD).pack(side="left")
            entry = ctk.CTkEntry(row, width=80, fg_color=FRAME_COLOR, border_color=ACCENT_PURPLE, justify="center")
            entry.insert(0, default_val)
            entry.pack(side="right")
            return entry

        self.hotkey_entry = add_setting_row(card, "Start/Stop Action:", self.hotkey_str)
        self.record_hotkey_entry = add_setting_row(card, "Start/Stop Record:", self.record_hotkey_str)
        self.exit_hotkey_entry = add_setting_row(card, "Emergency Exit:", self.exit_hotkey_str)
        
        ctk.CTkButton(
            card, text="APPLY SYSTEM CONFIG", command=self.save_hotkeys, 
            font=FONT_BOLD, fg_color=ACCENT_PURPLE, hover_color=ACCENT_CYAN, height=40
        ).pack(pady=15, padx=20, fill="x")

    def save_hotkeys(self):
        new_hotkey = self.hotkey_entry.get().strip().lower()
        new_record_hotkey = self.record_hotkey_entry.get().strip().lower()
        new_exit_hotkey = self.exit_hotkey_entry.get().strip().lower()
        if new_hotkey and new_record_hotkey and new_exit_hotkey:
            self.hotkey_str = new_hotkey
            self.record_hotkey_str = new_record_hotkey
            self.exit_hotkey_str = new_exit_hotkey
            self.update_status("CONFIG UPDATED", ACCENT_CYAN)
            hk_upper = self.hotkey_str.upper()
            rhk_upper = self.record_hotkey_str.upper()
            self.btn_clicker_start.configure(text=f"START ACTION [ {hk_upper} ]")
            self.btn_presser_start.configure(text=f"START ACTION [ {hk_upper} ]")
            self.play_btn.configure(text=f"PLAY SEQUENCE [ {hk_upper} ]")
            
            if self.recorder.is_recording:
                self.record_btn.configure(text=f"STOP REC [ {rhk_upper} ]")
            else:
                self.record_btn.configure(text=f"START REC [ {rhk_upper} ]")

    def save_config(self):
        config = {
            "btn_var": self.btn_var.get(),
            "click_h": self.click_h.get(), "click_m": self.click_m.get(),
            "click_s": self.click_s.get(), "click_ms": self.click_ms.get(),
            "click_repeat": self.click_repeat.get(),
            
            "key_entry": self.key_entry.get(),
            "key_h": self.key_h.get(), "key_m": self.key_m.get(),
            "key_s": self.key_s.get(), "key_ms": self.key_ms.get(),
            "key_repeat": self.key_repeat.get(),
            
            "playback_repeat": self.playback_repeat.get(),
            "hotkey_str": self.hotkey_str,
            "record_hotkey_str": self.record_hotkey_str,
            "exit_hotkey_str": self.exit_hotkey_str
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
            if "exit_hotkey_str" in config: self.exit_hotkey_str = config["exit_hotkey_str"]
            
            self._set_entry(self.hotkey_entry, self.hotkey_str)
            self._set_entry(self.record_hotkey_entry, self.record_hotkey_str)
            self._set_entry(self.exit_hotkey_entry, self.exit_hotkey_str)
            
            hk_upper = self.hotkey_str.upper()
            rhk_upper = self.record_hotkey_str.upper()
            self.btn_clicker_start.configure(text=f"START ACTION [ {hk_upper} ]")
            self.btn_presser_start.configure(text=f"START ACTION [ {hk_upper} ]")
            self.play_btn.configure(text=f"PLAY SEQUENCE [ {hk_upper} ]")
            self.record_btn.configure(text=f"START REC [ {rhk_upper} ]")
            
        except Exception as e:
            print("Error loading config:", e)
            
    def _set_entry(self, entry, value):
        entry.delete(0, 'end')
        entry.insert(0, str(value))

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = App()
    app.mainloop()
