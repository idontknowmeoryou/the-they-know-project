import os
import platform
import socket
import tkinter as tk
import psutil  # pip install psutil

# ---------------- Detect screen recording apps ----------------
recording_apps = [
    "obs64.exe", "obs32.exe", "streamlabs obs.exe", "xsplit.exe", "zoom.exe", "teams.exe"
]

def is_recording_app_running():
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in recording_apps:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

# ---------------- Gather system info ----------------
username = os.getlogin()
hostname = socket.gethostname()

try:
    local_ip = socket.gethostbyname(hostname)
except:
    local_ip = "Unknown"

if is_recording_app_running():
    local_ip = "Hidden (recording detected)"

os_info = platform.platform()  # OS version/brand

info_pairs = [
    ("User Name:", username),
    ("PC Name:", hostname),
    ("Local IP:", local_ip),
    ("OS Version / Brand:", os_info)
]

# ---------------- Tkinter full-screen UI ----------------
root = tk.Tk()
root.title("System Info")
root.attributes('-fullscreen', True)
root.config(cursor="none", bg="black")
root.bind("<Escape>", lambda e: root.destroy())

text_label = tk.Label(root, text="", fg="white", bg="black",
                      font=("Courier", 24), justify="left")
text_label.pack(expand=True, anchor="nw", padx=50, pady=50)

# ---------------- Display text slowly ----------------
label_speed = 50  # ms per character
lines_done = ""
pair_index = 0
char_index = 0
in_value = False

def type_text():
    global pair_index, char_index, in_value, lines_done
    if pair_index < len(info_pairs):
        label, value = info_pairs[pair_index]
        if not in_value:
            if char_index < len(label):
                lines_done += label[char_index]
                char_index += 1
                text_label.config(text=lines_done)
                root.after(label_speed, type_text)
            else:
                in_value = True
                char_index = 0
                root.after(label_speed, type_text)
        else:
            if char_index < len(value):
                lines_done += value[char_index]
                char_index += 1
                text_label.config(text=lines_done)
                root.after(label_speed, type_text)
            else:
                lines_done += "\n\n"
                text_label.config(text=lines_done)
                pair_index += 1
                char_index = 0
                in_value = False
                root.after(label_speed, type_text)
    else:
        text_label.config(text=lines_done)

type_text()
root.mainloop()