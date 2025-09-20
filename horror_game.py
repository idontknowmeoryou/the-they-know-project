import os
import platform
import socket
import psutil
import tkinter as tk
import pathlib
import pygame
import sys

# ---------------- Play Daisy_Bell.mp3 ----------------
mp3_path = pathlib.Path(__file__).parent / "Music" / "Daisy_Bell.mp3"
if mp3_path.exists():
    pygame.mixer.init()
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.set_volume(0.15)  # quiet
    pygame.mixer.music.play(-1)          # loop forever
else:
    print("Daisy_Bell.mp3 not found in Music folder.")

# ---------------- Gather system info ----------------
info_pairs = []

# User & system
username = os.getlogin()
home_dir = os.path.expanduser("~")
info_pairs.append(("Username:", username))
info_pairs.append(("Home Directory:", home_dir))
info_pairs.append(("Platform:", platform.platform()))
info_pairs.append(("System:", platform.system()))
info_pairs.append(("Release:", platform.release()))
info_pairs.append(("Version:", platform.version()))
info_pairs.append(("Machine:", platform.machine()))
info_pairs.append(("Processor:", platform.processor()))
mem_info = psutil.virtual_memory()
info_pairs.append(("Total Memory:", f"{round(mem_info.total / (1024**3),2)} GB"))

# CPU info
freq = psutil.cpu_freq()
if freq:
    info_pairs.append(("CPU Frequency:", f"{freq.current:.2f} MHz"))
info_pairs.append(("Logical cores:", str(psutil.cpu_count())))
info_pairs.append(("Physical cores:", str(psutil.cpu_count(logical=False))))

# Hostname & IP
hostname = socket.gethostname()
try:
    local_ip = socket.gethostbyname(hostname)
except:
    local_ip = "Unknown"
info_pairs.append(("Hostname:", hostname))
info_pairs.append(("Local IP:", local_ip))

# Network interfaces
for iface, addrs in psutil.net_if_addrs().items():
    ips = [a.address for a in addrs if a.family.name == 'AF_INET']
    if ips:
        info_pairs.append((f"Interface {iface} IPs:", ", ".join(ips)))

# Open network connections (first 5)
try:
    conns = psutil.net_connections()
    for i, c in enumerate(conns[:5]):
        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "?"
        info_pairs.append((f"Connection {i}:", f"{laddr} -> {raddr} ({c.status})"))
except:
    pass

# Processes (first 5 for readability)
try:
    processes = [p.info.get('name','<unknown>') for p in psutil.process_iter(['name'])]
except:
    processes = []
info_pairs.append(("Running processes (first 5):", ", ".join(processes[:5])))

# Disks
for disk in psutil.disk_partitions():
    try:
        usage = psutil.disk_usage(disk.mountpoint)
        info_pairs.append((f"Disk {disk.device} ({disk.fstype}):", 
                           f"{usage.total/(1024**3):.2f} GB total, {usage.free/(1024**3):.2f} GB free"))
    except:
        pass

# Battery
if hasattr(psutil, "sensors_battery"):
    battery = psutil.sensors_battery()
    if battery:
        info_pairs.append(("Battery percent:", f"{battery.percent}%"))
        info_pairs.append(("Charging:", str(battery.power_plugged)))

# Python info
info_pairs.append(("Python version:", sys.version))
info_pairs.append(("Python executable:", sys.executable))

# Environment variables (first 5 for readability)
env_items = list(os.environ.items())
for k, v in env_items[:5]:
    info_pairs.append((f"Env: {k}", v))

# ---------------- Tkinter UI ----------------
root = tk.Tk()
root.title("Full System Info")
root.attributes('-fullscreen', True)
root.config(cursor="none", bg="black")
root.bind("<Escape>", lambda e: root.destroy())

text_label = tk.Label(root, text="", fg="white", bg="black",
                      font=("Courier", 16), justify="left")
text_label.pack(expand=True, anchor="nw", padx=20, pady=20)

# ---------------- Display text slowly ----------------
label_speed = 30  # ms per character
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