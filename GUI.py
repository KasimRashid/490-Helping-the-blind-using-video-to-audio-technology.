import tkinter as tk
from tkinter import font as tkfont
import cv2
import threading
import time
from PIL import Image, ImageTk
from ultralytics import YOLO
from narration import make_sentence, speak
from database import save_detection_to_mysql, save_detection_to_json


#  main CONFIG
# ---------------------------------------------------
MODEL_PATH   = "yolo26n.pt"
FPS_CAP      = 30
FEED_W       = 720
FEED_H       = 480


#  THEME
# ---------------------------------------------------
BG         = "#0d0f14"
PANEL_BG   = "#13161e"
ACCENT     = "#00e5ff"
ACCENT_DIM = "#00838f"
TEXT       = "#e8eaf0"
TEXT_DIM   = "#5c6070"
DANGER     = "#ff4757"
SUCCESS    = "#2ed573"
BORDER     = "#1e2230"


class YOLOApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YOLO Vision Narrator")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.narration_on = True
        self.paused       = False
        self.model        = None

        self.frame_number = 0
        self.user_id      = "user_123"

        self.stream = cv2.VideoCapture(0)

        self.latest_labels  = []
        self.latest_message = ""
        self.annotated      = None
        self.yolo_lock      = threading.Lock()
        self.yolo_ready     = False

        self.fps_counter = 0
        self.fps_display = 0
        self.fps_time    = time.time()

        self._build_ui()

        threading.Thread(target=self._load_model, daemon=True).start()
        self._gui_loop()


    def _load_model(self):
        self.model = YOLO(MODEL_PATH)
        self.yolo_ready = True
        threading.Thread(target=self._yolo_loop, daemon=True).start()


    def _yolo_loop(self):
        while True:
            if self.paused:
                time.sleep(0.05)
                continue

            with self.yolo_lock:
                raw = self._latest_raw

            if raw is None:
                time.sleep(0.01)
                continue

            results = self.model(raw, verbose=False)

            labels = []
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                labels.append(self.model.names[cls_id])

            height, width = raw.shape[:2]
            self.frame_number += 1

            save_detection_to_json(
                self.frame_number,
                self.user_id,
                labels,
                width,
                height
            )

            save_detection_to_mysql(
                self.frame_number,
                self.user_id,
                labels,
                width,
                height
            )

            message = make_sentence(labels)
            annotated = results[0].plot()

            with self.yolo_lock:
                self.annotated = annotated
                self.latest_labels = labels
                self.latest_message = message

            if self.narration_on:
                speak(message)


    def _gui_loop(self):
        if not self.paused:
            ret, frame = self.stream.read()

            if ret:
                with self.yolo_lock:
                    self._latest_raw = frame.copy()
                    annotated = self.annotated
                    labels = list(self.latest_labels)
                    message = self.latest_message

                display = annotated if annotated is not None else frame

                rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb).resize((FEED_W, FEED_H), Image.LANCZOS)
                self._imtk = ImageTk.PhotoImage(image=img)
                self.canvas.itemconfig(self._canvas_img_id, image=self._imtk)

                self.fps_counter += 1
                now = time.time()
                if now - self.fps_time >= 1.0:
                    self.fps_display = self.fps_counter
                    self.fps_counter = 0
                    self.fps_time = now

                self.fps_label.config(text=f"FPS: {self.fps_display}")

                unique = list(dict.fromkeys(labels))
                self.narration_var.set(message or "Waiting…")
                self.objects_var.set("\n".join(f"• {l}" for l in unique) if unique else "—")
                self.count_var.set(f"Objects : {len(labels)}\nUnique   : {len(unique)}")

        self.root.after(max(1, int(1000 / FPS_CAP)), self._gui_loop)


    def _build_ui(self):
        title_font  = tkfont.Font(family="Courier New", size=13, weight="bold")
        label_font  = tkfont.Font(family="Courier New", size=9)
        narr_font   = tkfont.Font(family="Courier New", size=11, weight="bold")
        status_font = tkfont.Font(family="Courier New", size=8)
        btn_font    = tkfont.Font(family="Courier New", size=9, weight="bold")

        header = tk.Frame(self.root, bg=BG, pady=10)
        header.pack(fill="x", padx=16)

        tk.Label(
            header,
            text="◈  YOLO VISION NARRATOR",
            font=title_font,
            fg=ACCENT,
            bg=BG
        ).pack(side="left")

        self.fps_label = tk.Label(
            header,
            text="FPS: --",
            font=status_font,
            fg=TEXT_DIM,
            bg=BG
        )
        self.fps_label.pack(side="right", padx=4)

        tk.Label(header, text="●", font=status_font, fg=SUCCESS, bg=BG).pack(side="right")

        main_row = tk.Frame(self.root, bg=BG)
        main_row.pack(padx=16, pady=(0, 12))

        feed_wrapper = tk.Frame(
            main_row,
            bg=BORDER,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        feed_wrapper.pack(side="left")

        self.canvas = tk.Canvas(
            feed_wrapper,
            width=FEED_W,
            height=FEED_H,
            bg="#08090d",
            highlightthickness=0
        )
        self.canvas.pack()

        self._canvas_img_id = self.canvas.create_image(0, 0, anchor="nw")
        self._imtk = None
        self._latest_raw = None

        right = tk.Frame(main_row, bg=BG, width=220)
        right.pack(side="left", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        def section(parent, title):
            f = tk.Frame(
                parent,
                bg=PANEL_BG,
                highlightthickness=1,
                highlightbackground=BORDER
            )
            f.pack(fill="x", pady=(0, 10), ipady=8, ipadx=8)

            tk.Label(
                f,
                text=title,
                font=status_font,
                fg=ACCENT_DIM,
                bg=PANEL_BG
            ).pack(anchor="w", padx=8, pady=(6, 2))

            return f

        narr_sec = section(right, "▸ NARRATION")
        self.narration_var = tk.StringVar(value="Waiting…")

        tk.Label(
            narr_sec,
            textvariable=self.narration_var,
            font=narr_font,
            fg=TEXT,
            bg=PANEL_BG,
            wraplength=195,
            justify="left"
        ).pack(anchor="w", padx=8, pady=(0, 6))

        obj_sec = section(right, "▸ DETECTED OBJECTS")
        self.objects_var = tk.StringVar(value="—")

        tk.Label(
            obj_sec,
            textvariable=self.objects_var,
            font=label_font,
            fg=TEXT,
            bg=PANEL_BG,
            wraplength=195,
            justify="left"
        ).pack(anchor="w", padx=8, pady=(0, 6))

        count_sec = section(right, "▸ STATS")
        self.count_var = tk.StringVar(value="Objects : 0\nUnique   : 0")

        tk.Label(
            count_sec,
            textvariable=self.count_var,
            font=label_font,
            fg=TEXT,
            bg=PANEL_BG,
            justify="left"
        ).pack(anchor="w", padx=8, pady=(0, 6))

        ctrl_sec = section(right, "▸ CONTROLS")
        ctrl_inner = tk.Frame(ctrl_sec, bg=PANEL_BG)
        ctrl_inner.pack(fill="x", padx=8, pady=(0, 6))

        def btn(parent, text, cmd, color=ACCENT):
            b = tk.Button(
                parent,
                text=text,
                command=cmd,
                font=btn_font,
                fg=BG,
                bg=color,
                activeforeground=BG,
                activebackground=color,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=8,
                pady=5
            )
            b.pack(fill="x", pady=2)
            return b

        self.pause_btn = btn(ctrl_inner, "⏸  PAUSE", self._toggle_pause, ACCENT)
        self.narr_btn = btn(ctrl_inner, "🔊  NARRATION: ON", self._toggle_narration, ACCENT_DIM)
        btn(ctrl_inner, "✕  QUIT", self._quit, DANGER)

        tk.Label(
            self.root,
            text="model: yolo26n",
            font=status_font,
            fg=TEXT_DIM,
            bg=BG
        ).pack(pady=(0, 8))


    def _toggle_pause(self):
        self.paused = not self.paused

        self.pause_btn.config(
            text="▶  RESUME" if self.paused else "⏸  PAUSE",
            bg=SUCCESS if self.paused else ACCENT
        )


    def _toggle_narration(self):
        self.narration_on = not self.narration_on

        self.narr_btn.config(
            text="🔊  NARRATION: ON" if self.narration_on else "🔇  NARRATION: OFF",
            bg=ACCENT_DIM if self.narration_on else BORDER
        )


    def _quit(self):
        self.stream.release()
        self.root.destroy()


    def on_close(self):
        self._quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()