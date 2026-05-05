# Everything fits (Kasim features + my features)
# Keeps male voice as default but female voice is just male voice with a different accent


import tkinter as tk
from tkinter import font as tkfont
import cv2
import threading
import time
from PIL import Image, ImageTk
from ultralytics import YOLO
from narration2 import make_sentence, speak

# --- THEME & CONFIG ---
MODEL_PATH, FPS_CAP, FEED_W, FEED_H = "yolo26n.pt", 30, 720, 480
BG, PANEL_BG, ACCENT, ACCENT_DIM, BORDER, TEXT, TEXT_DIM, DANGER, SUCCESS = \
    "#0d0f14", "#13161e", "#00e5ff", "#00838f", "#1e2230", "#e8eaf0", "#5c6070", "#ff4757", "#2ed573"

class YOLOApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YOLO Vision Narrator")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Control flags and Audio state
        self.narration_on, self.paused, self.running = True, False, True
        self.voice_speed, self.voice_index = 160, 1 
        
        self.stream = cv2.VideoCapture(0)
        self.latest_labels, self.latest_message, self.annotated = [], "", None
        self.yolo_lock = threading.Lock()
        self._latest_raw = None

        self.fps_counter, self.fps_display, self.fps_time = 0, 0, time.time()

        self._build_ui()
        threading.Thread(target=self._load_model, daemon=True).start()
        self._gui_loop()

    def _load_model(self):
        self.model = YOLO(MODEL_PATH)
        threading.Thread(target=self._yolo_loop, daemon=True).start()

    def _yolo_loop(self):
        # Using self.running to prevent "core dumped" on exit
        while self.running:
            if self.paused:
                time.sleep(0.05)
                continue
            with self.yolo_lock:
                raw = self._latest_raw
            if raw is None:
                time.sleep(0.01)
                continue

            results = self.model(raw, verbose=False)
            labels = [self.model.names[int(box.cls[0])] for box in results[0].boxes]
            message = make_sentence(labels)
            annotated = results[0].plot()

            with self.yolo_lock:
                self.annotated, self.latest_labels, self.latest_message = annotated, labels, message

            # Narration style from GUI.py: heard only when objects are introduced
            # (Terminal printing is removed to follow your instructions)
            if self.narration_on:
                speak(message, rate=self.voice_speed, voice_index=self.voice_index)

    def _gui_loop(self):
        if not self.paused:
            ret, frame = self.stream.read()
            if ret:
                with self.yolo_lock:
                    self._latest_raw = frame.copy()
                    display = self.annotated if self.annotated is not None else frame
                    labels, message = list(self.latest_labels), self.latest_message

                rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb).resize((FEED_W, FEED_H), Image.LANCZOS)
                self._imtk = ImageTk.PhotoImage(image=img)
                self.canvas.itemconfig(self._canvas_img_id, image=self._imtk)

                self.fps_counter += 1
                now = time.time()
                if now - self.fps_time >= 1.0:
                    self.fps_display, self.fps_counter, self.fps_time = self.fps_counter, 0, now
                self.fps_label.config(text=f"FPS: {self.fps_display}")

                unique = list(dict.fromkeys(labels))
                self.narration_var.set(message or "Waiting…")
                self.objects_var.set("\n".join(f"• {l}" for l in unique) if unique else "—")
                self.count_var.set(f"Objects : {len(labels)} | Unique : {len(unique)}")

        self.root.after(max(1, int(1000 / FPS_CAP)), self._gui_loop)

    def _build_ui(self):
        title_font = tkfont.Font(family="Courier New", size=12, weight="bold")
        narr_font = tkfont.Font(family="Courier New", size=10, weight="bold")
        status_font = tkfont.Font(family="Courier New", size=8)
        btn_font = tkfont.Font(family="Courier New", size=9, weight="bold")

        header = tk.Frame(self.root, bg=BG, pady=5)
        header.pack(fill="x", padx=16)
        tk.Label(header, text="◈ YOLO VISION NARRATOR", font=title_font, fg=ACCENT, bg=BG).pack(side="left")
        self.fps_label = tk.Label(header, text="FPS: --", font=status_font, fg=TEXT_DIM, bg=BG)
        self.fps_label.pack(side="right", padx=4)

        main_row = tk.Frame(self.root, bg=BG)
        main_row.pack(padx=16, pady=(0, 5))
        
        feed_wrapper = tk.Frame(main_row, bg=BORDER, highlightthickness=1)
        feed_wrapper.pack(side="left")
        self.canvas = tk.Canvas(feed_wrapper, width=FEED_W, height=FEED_H, bg="#08090d", highlightthickness=0)
        self.canvas.pack()
        self._canvas_img_id = self.canvas.create_image(0, 0, anchor="nw")

        # Sidebar width set to 240 to fit all controls perfectly
        right = tk.Frame(main_row, bg=BG, width=240)
        right.pack(side="left", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        def section(title, pady_int=2):
            f = tk.Frame(right, bg=PANEL_BG, highlightthickness=1, highlightbackground=BORDER)
            f.pack(fill="x", pady=(0, 5), ipady=pady_int)
            tk.Label(f, text=title, font=status_font, fg=ACCENT_DIM, bg=PANEL_BG).pack(anchor="w", padx=6, pady=(2, 2))
            return f

        # Compacted sections for layout consistency
        narr_sec = section("▸ NARRATION")
        self.narration_var = tk.StringVar(value="Waiting…")
        tk.Label(narr_sec, textvariable=self.narration_var, font=narr_font, fg=TEXT, bg=PANEL_BG, wraplength=210, justify="left").pack(anchor="w", padx=8)

        obj_sec = section("▸ DETECTED")
        self.objects_var = tk.StringVar(value="—")
        tk.Label(obj_sec, textvariable=self.objects_var, font=status_font, fg=TEXT, bg=PANEL_BG, justify="left").pack(anchor="w", padx=8)

        count_sec = section("▸ STATS")
        self.count_var = tk.StringVar(value="Objects : 0 | Unique : 0")
        tk.Label(count_sec, textvariable=self.count_var, font=status_font, fg=TEXT, bg=PANEL_BG).pack(anchor="w", padx=8)

        ctrl_sec = section("▸ CONTROLS")
        self.pause_btn = tk.Button(ctrl_sec, text="⏸ PAUSE", command=self._toggle_pause, font=btn_font, bg=ACCENT, fg=BG, relief="flat")
        self.pause_btn.pack(fill="x", padx=8, pady=1)
        self.narr_btn = tk.Button(ctrl_sec, text="🔊 NARR: ON", command=self._toggle_narration, font=btn_font, bg=ACCENT_DIM, fg=BG, relief="flat")
        self.narr_btn.pack(fill="x", padx=8, pady=1)

        # Audio Settings Section
        audio_sec = section("▸ AUDIO SETTINGS", pady_int=5)
        tk.Label(audio_sec, text="Voice Speed", font=status_font, fg=TEXT, bg=PANEL_BG).pack(anchor="w", padx=8)
        
        self.speed_scale = tk.Scale(audio_sec, from_=100, to_=300, orient="horizontal",
                                    bg=PANEL_BG, fg=ACCENT, troughcolor=BG, 
                                    highlightthickness=1, highlightbackground=BORDER,
                                    command=self._update_speed, showvalue=False, bd=0)
        self.speed_scale.set(self.voice_speed)
        self.speed_scale.pack(fill="x", padx=10)
        
        self.speed_label = tk.Label(audio_sec, text=str(self.voice_speed), font=btn_font, fg=ACCENT, bg=PANEL_BG)
        self.speed_label.pack()

        # Male and Female buttons
        v_frame = tk.Frame(audio_sec, bg=PANEL_BG)
        v_frame.pack(fill="x", padx=10, pady=2)
        self.m_btn = tk.Button(v_frame, text="MALE", command=lambda: self._set_voice(0), 
                               font=btn_font, bg=PANEL_BG, fg=TEXT, 
                               highlightthickness=1, highlightbackground=TEXT, relief="flat")
        self.m_btn.pack(side="left", expand=True, fill="x", padx=2)
        
        self.f_btn = tk.Button(v_frame, text="FEMALE", command=lambda: self._set_voice(1), 
                               font=btn_font, bg=ACCENT_DIM, fg=BG, 
                               highlightthickness=1, highlightbackground=ACCENT, relief="flat")
        self.f_btn.pack(side="left", expand=True, fill="x", padx=2)

        tk.Button(ctrl_sec, text="✕ QUIT", command=self._quit, font=btn_font, bg=DANGER, fg=BG, relief="flat").pack(fill="x", padx=8, pady=1)

    def _update_speed(self, val):
        self.voice_speed = int(val)
        self.speed_label.config(text=val)

    def _set_voice(self, idx):
        # Switches voice index and updates button visuals
        self.voice_index = idx
        if idx == 0:
            self.m_btn.config(bg=ACCENT_DIM, fg=BG, highlightbackground=ACCENT)
            self.f_btn.config(bg=PANEL_BG, fg=TEXT, highlightbackground=TEXT)
        else:
            self.f_btn.config(bg=ACCENT_DIM, fg=BG, highlightbackground=ACCENT)
            self.m_btn.config(bg=PANEL_BG, fg=TEXT, highlightbackground=TEXT)

    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="▶ RESUME" if self.paused else "⏸ PAUSE", bg=SUCCESS if self.paused else ACCENT)

    def _toggle_narration(self):
        self.narration_on = not self.narration_on
        self.narr_btn.config(text="🔊 NARRATION: ON" if self.narration_on else "🔇 NARRATION: OFF", bg=ACCENT_DIM if self.narration_on else BORDER)

    def _quit(self):
        # Proper shutdown sequence to prevent core dump
        self.running = False
        time.sleep(0.2) # Wait for YOLO thread to exit
        self.stream.release()
        self.root.destroy()

    def on_close(self):
        self._quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()