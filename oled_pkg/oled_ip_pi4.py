#!/usr/bin/env python3

import time
import subprocess
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

# -------------------------------------------------
# OLED Setup
# -------------------------------------------------
RST = None
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

disp.begin()
disp.clear()
disp.display()

width = disp.width
height = disp.height

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

font = ImageFont.load_default()
padding = -2
top = padding
x = 0


# -------------------------------------------------
# Helper Functions
# -------------------------------------------------

def get_wifi_ssid():
    try:
        ssid = subprocess.check_output(
            "iwgetid -r",
            shell=True
        ).decode().strip()
        return "WIFI: " + (ssid.upper() if ssid else "NO NETWORK")
    except:
        return "WIFI: NO NETWORK"


def get_ip():
    try:
        ip = subprocess.check_output(
            "ip -4 addr show wlan0 | awk '/inet / {print $2}' | cut -d/ -f1",
            shell=True
        ).decode().strip()
        return "IP: " + (ip if ip else "NO IP")
    except:
        return "IP: NO IP"


def get_memory():
    """Read memory directly from /proc/meminfo (faster than free -m)"""
    try:
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, value = line.split(":")
                meminfo[key] = int(value.split()[0])

        total = meminfo["MemTotal"] // 1024
        available = meminfo["MemAvailable"] // 1024
        used = total - available
        percent = (used / total) * 100

        return f"MEM:{used}/{total}MB {percent:.0f}%"
    except:
        return "MEM:N/A"


# ---------- CPU Monitoring using /proc/stat ----------

def read_cpu_times():
    with open("/proc/stat", "r") as f:
        values = list(map(int, f.readline().split()[1:]))

    idle = values[3]
    total = sum(values)
    return idle, total


def get_cpu_usage(prev_idle, prev_total):
    idle, total = read_cpu_times()

    idle_delta = idle - prev_idle
    total_delta = total - prev_total

    if total_delta == 0:
        usage = 0.0
    else:
        usage = 100 * (1 - idle_delta / total_delta)

    # Load average (1 minute)
    with open("/proc/loadavg", "r") as f:
        load = f.read().split()[0]

    cpu_text = f"CPU:{usage:.0f}% L:{load}"
    return cpu_text, idle, total


# -------------------------------------------------
# Main Loop
# -------------------------------------------------

prev_idle, prev_total = read_cpu_times()

while True:

    # Clear display
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Gather info
    network = get_wifi_ssid()
    ip = get_ip()
    mem = get_memory()
    cpu, prev_idle, prev_total = get_cpu_usage(prev_idle, prev_total)

    # Draw text
    draw.text((x, top),      network, font=font, fill=255)
    draw.text((x, top + 8),  ip,      font=font, fill=255)
    draw.text((x, top + 16), mem,     font=font, fill=255)
    draw.text((x, top + 25), cpu,     font=font, fill=255)

    # Show on OLED
    disp.image(image)
    disp.display()

    time.sleep(1)
