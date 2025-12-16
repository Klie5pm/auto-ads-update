import tkinter as tk
from tkinter import ttk
import threading
import pyautogui
import keyboard
import time
import json
import os

running = False
picking = False
current_pick_target = None
dark_mode = False

CONFIG_FILE = "config.json"

# ====================================================
# SAVE / LOAD CONFIG (TẤT CẢ THÔNG SỐ)
# ====================================================

def save_config():
    data = {
        "insert_x": insert_x.get(),
        "insert_y": insert_y.get(),
        "timestamp_x": timestamp_x.get(),
        "timestamp_y": timestamp_y.get(),
        "interval_ms": interval_ms.get(),
        "video_length": video_length.get(),
        "repeat_mode": repeat_mode.get(),
        "repeat_count": repeat_count.get(),
        "start_key": start_key.get(),
        "stop_key": stop_key.get(),
        "dark_mode": dark_mode,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

    status.set("💾 Saved all settings!")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)

            insert_x.set(data.get("insert_x", 564))
            insert_y.set(data.get("insert_y", 358))
            timestamp_x.set(data.get("timestamp_x", 536))
            timestamp_y.set(data.get("timestamp_y", 741))
            interval_ms.set(data.get("interval_ms", 200))
            video_length.set(data.get("video_length", ""))
            repeat_mode.set(data.get("repeat_mode", False))
            repeat_count.set(data.get("repeat_count", 1))
            start_key.set(data.get("start_key", "F6"))
            stop_key.set(data.get("stop_key", "F7"))

            if data.get("dark_mode", False):
                global dark_mode
                if not dark_mode:
                    toggle_dark_mode()

            status.set("📂 Loaded saved settings!")
        except Exception:
            status.set("⚠ Error loading config file")


# ====================================================
# HOTKEY CONTROL
# ====================================================

def disable_all_hotkeys():
    """Tắt toàn bộ hotkey tạm thời (để user đổi phím an toàn)"""
    try:
        for hk in keyboard._hotkeys.copy():
            keyboard.remove_hotkey(hk)
    except:
        pass


def update_hotkeys():
    """Chỉ bật hotkey sau khi user SAVE ALL"""
    disable_all_hotkeys()

    keyboard.add_hotkey(start_key.get(), start_auto)
    keyboard.add_hotkey(stop_key.get(), stop_auto)


# ====================================================
# PICK POSITION
# ====================================================

def start_pick(target):
    global picking, current_pick_target

    picking = True
    current_pick_target = target
    status.set("🟡 Move mouse to choose location, then click...")

    tooltip = tk.Toplevel()
    tooltip.overrideredirect(True)
    tooltip.attributes("-topmost", True)

    tooltip_label = tk.Label(
        tooltip, text="X: 0  Y: 0", bg="#000", fg="#FFF",
        padx=6, pady=3, font=("Segoe UI", 9)
    )
    tooltip_label.pack()

    def update_tooltip():
        while picking:
            x, y = pyautogui.position()
            tooltip_label.config(text=f"X: {x}  Y: {y}")
            tooltip.geometry(f"+{x+15}+{y+15}")
            time.sleep(0.01)

    threading.Thread(target=update_tooltip, daemon=True).start()

    def on_click(event):
        global picking
        mx, my = pyautogui.position()

        if current_pick_target == "timestamp":
            timestamp_x.set(mx)
            timestamp_y.set(my)
        else:
            insert_x.set(mx)
            insert_y.set(my)

        picking = False
        tooltip.destroy()
        status.set("✅ Picked!")

        keyboard.unhook_all()

    keyboard.on_click(on_click)


# ====================================================
# AUTO LOOP
# ====================================================

def auto_run():
    global running
    loops = 0

    while running:
        pyautogui.click(timestamp_x.get(), timestamp_y.get())
        time.sleep(0.01)

        for _ in range(3):
            pyautogui.press("up")
            time.sleep(0.005)

        pyautogui.click(insert_x.get(), insert_y.get())

        loops += 1
        status.set(f"🔁 Loop: {loops}")

        if repeat_mode.get() and loops >= repeat_count.get():
            running = False
            status.set(f"⏹ Completed {loops} loops")
            return

        time.sleep(interval_ms.get() / 1000)


def start_auto():
    global running

    if running:
        status.set("⚠ Tool is already running")
        return

    try:
        val = int(interval_ms.get())
        if val <= 0 or val > 200:
            status.set("⚠ Interval must be 1–200 ms")
            return
    except:
        status.set("⚠ Interval invalid")
        return

    running = True
    status.set("▶ Running...")
    threading.Thread(target=auto_run, daemon=True).start()


def stop_auto():
    global running
    running = False
    status.set("⏹ Stopped")


# ====================================================
# CALCULATE LOOPS
# ====================================================

def calculate_loops():
    raw = video_length.get().strip().zfill(6)

    hh = int(raw[:2])
    mm = int(raw[2:4])
    ss = int(raw[4:6])

    total = hh * 3600 + mm * 60 + ss
    start = 90
    step = 180

    loops = (total - start) // step
    loops = max(0, loops)

    repeat_count.set(loops)
    repeat_mode.set(True)

    status.set(f"📌 {hh:02d}:{mm:02d}:{ss:02d} → {loops} loops")


# ====================================================
# CUSTOM BUTTON (Rounded)
# ====================================================

def rounded_button(parent, text, command, x, y,
                   w=120, h=38, radius=12,
                   bg="#E0E0E0", fg="#000"):
    canvas = tk.Canvas(parent, width=w, height=h,
                       bg=parent["bg"], highlightthickness=0)
    canvas.place(x=x, y=y)

    canvas.create_arc((0, 0, radius*2, radius*2), start=90, extent=90, fill=bg, outline=bg)
    canvas.create_arc((w-radius*2, 0, w, radius*2), start=0, extent=90, fill=bg, outline=bg)
    canvas.create_arc((0, h-radius*2, radius*2, h), start=180, extent=90, fill=bg, outline=bg)
    canvas.create_arc((w-radius*2, h-radius*2, w, h), start=270, extent=90, fill=bg, outline=bg)

    canvas.create_rectangle(radius, 0, w-radius, h, fill=bg, outline=bg)
    canvas.create_rectangle(0, radius, w, h-radius, fill=bg, outline=bg)

    canvas.create_text(w/2, h/2, text=text, font=("Segoe UI", 10, "bold"), fill=fg)

    canvas.bind("<Button-1>", lambda e: command())

    return canvas


# ====================================================
# DARK MODE BUTTON
# ====================================================

def redraw_darkmode_button(bg, fg):
    dark_button_canvas.delete("all")
    w, h = 120, 32
    r = 12

    dark_button_canvas.create_arc((0, 0, r*2, r*2), start=90, extent=90, fill=bg, outline=bg)
    dark_button_canvas.create_arc((w-r*2, 0, w, r*2), start=0, extent=90, fill=bg, outline=bg)
    dark_button_canvas.create_arc((0, h-r*2, r*2, h), start=180, extent=90, fill=bg, outline=bg)
    dark_button_canvas.create_arc((w-r*2, h-r*2, w, h), start=270, extent=90, fill=bg, outline=bg)

    dark_button_canvas.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
    dark_button_canvas.create_rectangle(0, r, w, h-r, fill=bg, outline=bg)

    dark_button_canvas.create_text(w/2, h/2, text="Dark Mode",
                                   font=("Segoe UI", 10, "bold"), fill=fg)


def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode

    if dark_mode:
        root.config(bg="#1F1F1F")
        status_label.config(bg="#2A2A2A", fg="#FFFFFF")
        copyright_label.config(bg="#1F1F1F", fg="#AAAAAA")
        card.config(style="Dark.TLabelframe")
        dark_button_canvas.config(bg="#1F1F1F")
        redraw_darkmode_button("#3A3A3A", "#FFFFFF")
    else:
        root.config(bg="#EFEFEF")
        status_label.config(bg="#DDDDDD", fg="#333333")
        copyright_label.config(bg="#EFEFEF", fg="#444")
        card.config(style="Card.TLabelframe")
        dark_button_canvas.config(bg="#EFEFEF")
        redraw_darkmode_button("#D9D9D9", "#000000")


# ====================================================
# UI SETUP
# ====================================================

root = tk.Tk()
root.title("Auto Ads (V7.3) — By KienNTX")
root.geometry("500x480")
root.resizable(False, False)

try:
    root.iconbitmap("YouTube_logo.ico")
except:
    pass

style = ttk.Style()
style.theme_use("clam")

style.configure("Card.TLabelframe", background="#FFFFFF", foreground="#333333")
style.configure("Card.TLabelframe.Label", background="#FFFFFF", font=("Segoe UI", 11, "bold"))

style.configure("Dark.TLabelframe", background="#1F1F1F", foreground="#FFFFFF")
style.configure("Dark.TLabelframe.Label", background="#1F1F1F", foreground="#FFFFFF")


# Variables
insert_x = tk.IntVar(value=564)
insert_y = tk.IntVar(value=358)
timestamp_x = tk.IntVar(value=536)
timestamp_y = tk.IntVar(value=741)
interval_ms = tk.IntVar(value=200)

start_key = tk.StringVar(value="F6")
stop_key = tk.StringVar(value="F7")

video_length = tk.StringVar()
repeat_mode = tk.BooleanVar(value=False)
repeat_count = tk.IntVar(value=1)

interval_msg = tk.StringVar(value="")


def validate_interval(*args):
    try:
        val = int(interval_ms.get())
        if val <= 0 or val > 200:
            interval_msg.set("Chỉ được 0 < ms ≤ 200")
        else:
            interval_msg.set("")
    except:
        if str(interval_ms.get()).strip() == "":
            interval_msg.set("")
        else:
            interval_msg.set("Nhập số ms")


interval_ms.trace_add("write", lambda *args: validate_interval())


# DARK MODE BUTTON
dark_button_canvas = tk.Canvas(root, width=120, height=32,
                               bg=root["bg"], highlightthickness=0)
dark_button_canvas.place(x=350, y=10)
redraw_darkmode_button("#D9D9D9", "#000000")
dark_button_canvas.bind("<Button-1>", lambda e: toggle_dark_mode())


# MAIN PANEL
card = ttk.LabelFrame(root, text=" Auto Ads Settings ", padding=15, style="Card.TLabelframe")
card.place(x=15, y=60, width=470, height=310)

row = 0
ttk.Label(card, text="Insert position:").grid(row=row, column=0, sticky="w", pady=4)
ttk.Entry(card, textvariable=insert_x, width=8).grid(row=row, column=1, padx=4)
ttk.Entry(card, textvariable=insert_y, width=8).grid(row=row, column=2, padx=4)
ttk.Button(card, text="Pick", width=6, command=lambda: start_pick("insert")).grid(row=row, column=3, padx=2)

row += 1
ttk.Label(card, text="Timestamp position:").grid(row=row, column=0, sticky="w", pady=4)
ttk.Entry(card, textvariable=timestamp_x, width=8).grid(row=row, column=1, padx=4)
ttk.Entry(card, textvariable=timestamp_y, width=8).grid(row=row, column=2, padx=4)
ttk.Button(card, text="Pick", width=6, command=lambda: start_pick("timestamp")).grid(row=row, column=3, padx=2)

row += 1
ttk.Label(card, text="Interval (ms):").grid(row=row, column=0, sticky="w", pady=4)
ttk.Entry(card, textvariable=interval_ms, width=8).grid(row=row, column=1, padx=4)
ttk.Label(card, textvariable=interval_msg, foreground="red").grid(row=row, column=2, columnspan=3, sticky="w")

row += 1
ttk.Label(card, text="Video length (HHMMSS):").grid(row=row, column=0, sticky="w", pady=4)
ttk.Entry(card, textvariable=video_length, width=8).grid(row=row, column=1, padx=4)
ttk.Button(card, text="Calc", width=6, command=calculate_loops).grid(row=row, column=2, padx=2)

row += 1
ttk.Checkbutton(card, text="Repeat loops", variable=repeat_mode).grid(row=row, column=0, sticky="w", pady=4)
ttk.Entry(card, textvariable=repeat_count, width=8).grid(row=row, column=1, padx=4)

row += 1
ttk.Label(card, text="Start key:").grid(row=row, column=0, sticky="w", pady=4)
start_entry = ttk.Entry(card, textvariable=start_key, width=10)
start_entry.grid(row=row, column=1, padx=4)

ttk.Label(card, text="Stop key:").grid(row=row, column=2, sticky="w")
stop_entry = ttk.Entry(card, textvariable=stop_key, width=10)
stop_entry.grid(row=row, column=3, padx=4)


def make_hotkey_capture(entry, var):
    def on_key(event):
        disable_all_hotkeys()  # TẮT HOTKEY TRONG LÚC ĐỔI
        key = event.keysym

        # Không cho chọn phím mũi tên / modifier
        if key in ["Up", "Down", "Left", "Right",
                   "Shift_L", "Shift_R",
                   "Control_L", "Control_R",
                   "Alt_L", "Alt_R"]:
            return "break"

        var.set(key)
        return "break"

    entry.bind("<Key>", on_key)


make_hotkey_capture(start_entry, start_key)
make_hotkey_capture(stop_entry, stop_key)


row += 1
ttk.Button(card, text="Save all", command=lambda: (update_hotkeys(), save_config())).grid(
    row=row, column=0, columnspan=4, pady=12
)


# START / STOP BUTTONS
rounded_button(root, "START", start_auto, x=90, y=390)
rounded_button(root, "STOP", stop_auto, x=270, y=390)


# STATUS + COPYRIGHT
status = tk.StringVar(value="Ready...")

status_label = tk.Label(root, textvariable=status,
                        bg="#DDDDDD", fg="#333333",
                        anchor="w", font=("Segoe UI", 9))
status_label.place(x=0, y=460, width=500, height=20)

copyright_label = tk.Label(
    root,
    text="Developed by KienNTX © 2025",
    bg="#EFEFEF", fg="#444",
    font=("Segoe UI", 9)
)
copyright_label.place(x=0, y=440, width=500)


# LOAD SAVED SETTINGS
load_config()

# KHÔNG BẬT HOTKEY CHO TỚI KHI USER BẤM SAVE ALL
disable_all_hotkeys()

root.mainloop()
