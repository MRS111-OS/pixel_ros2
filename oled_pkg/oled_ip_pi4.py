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
    """Read memory directly from /proc/meminfo"""
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


# ---------- CPU Monitoring ----------

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

    # Load average
    with open("/proc/loadavg", "r") as f:
        load = f.read().split()[0]

    cpu_text = f"CPU:{usage:.0f}% L:{load}"
    return cpu_text, idle, total


# ---------- CPU Temperature ----------

def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_raw = int(f.read().strip())

        temp_c = temp_raw / 1000.0
        return f"T:{temp_c:.1f}C"
    except:
        return "T:N/A"


# -------------------------------------------------
# Main Loop
# -------------------------------------------------

prev_idle, prev_total = read_cpu_times()

while True:

    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    network = get_wifi_ssid()
    ip = get_ip()
    mem = get_memory()
    cpu, prev_idle, prev_total = get_cpu_usage(prev_idle, prev_total)
    temp = get_temperature()

    draw.text((x, top),      network, font=font, fill=255)
    draw.text((x, top + 8),  ip,      font=font, fill=255)
    draw.text((x, top + 16), mem,     font=font, fill=255)

    # CPU + Temperature on same line
    draw.text((x, top + 25), cpu + " " + temp, font=font, fill=255)

    disp.image(image)
    disp.display()

    time.sleep(1)