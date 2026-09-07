#!/usr/bin/env python3

import time
import subprocess
import signal
import sys

from luma.core.interface.serial import i2c
from luma.oled.device import sh1106

from PIL import Image, ImageDraw, ImageFont

# -------------------------------------------------
# OLED Setup
# -------------------------------------------------

# Change address to 0x3D if required
serial = i2c(port=1, address=0x3C)

# SH1106 128x64 OLED
device = sh1106(serial)

width = device.width
height = device.height

# Create image buffer
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# -------------------------------------------------
# Font Setup (~10% smaller)
# -------------------------------------------------

try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        9
    )
except:
    font = ImageFont.load_default()

# -------------------------------------------------
# Layout
# -------------------------------------------------

left_margin = 2
top_margin = 3
line_spacing = 15

# -------------------------------------------------
# Graceful Shutdown
# -------------------------------------------------

running = True

def signal_handler(sig, frame):
    global running

    print("\nStopping OLED updater...")
    print("Leaving last frame on OLED.")

    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------

def get_wifi_ssid():
    try:
        ssid = subprocess.check_output(
            "iwgetid -r",
            shell=True
        ).decode().strip()

        return "  WIFI: " + (
            ssid.upper() if ssid else "NO NETWORK"
        )

    except:
        return "  WIFI: ERROR"


def get_ip():
    try:
        ip = subprocess.check_output(
            "ip -4 addr show wlan0 | awk '/inet / {print $2}' | cut -d/ -f1",
            shell=True
        ).decode().strip()

        return "  IP: " + (
            ip if ip else "NO IP"
        )

    except:
        return "  IP: ERROR"


def get_memory():

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

        return f"  MEM:{used}/{total}MB {percent:.0f}%"

    except:
        return "  MEM: ERROR"


# -------------------------------------------------
# CPU Usage
# -------------------------------------------------

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
        usage = 100 * (
            1 - idle_delta / total_delta
        )

    return f"CPU:{usage:.0f}%", idle, total


# -------------------------------------------------
# Temperature
# -------------------------------------------------

def get_temperature():

    try:
        with open(
            "/sys/class/thermal/thermal_zone0/temp",
            "r"
        ) as f:

            temp_raw = int(f.read().strip())

        temp_c = temp_raw / 1000.0

        return f"T:{temp_c:.1f}C"

    except:
        return "T:ERR"


# -------------------------------------------------
# Main Loop
# -------------------------------------------------

prev_idle, prev_total = read_cpu_times()

while running:

    # Clear framebuffer
    draw.rectangle(
        (0, 0, width, height),
        outline=0,
        fill=0
    )

    # Read system data
    network = get_wifi_ssid()
    ip = get_ip()
    mem = get_memory()

    cpu, prev_idle, prev_total = get_cpu_usage(
        prev_idle,
        prev_total
    )

    temp = get_temperature()

    # Draw lines
    draw.text(
        (left_margin, top_margin),
        network,
        font=font,
        fill=255
    )

    draw.text(
        (left_margin, top_margin + line_spacing),
        ip,
        font=font,
        fill=255
    )

    draw.text(
        (left_margin, top_margin + line_spacing * 2),
        mem,
        font=font,
        fill=255
    )

    draw.text(
        (left_margin, top_margin + line_spacing * 3),
        "  " + cpu + " " + temp,
        font=font,
        fill=255
    )

    # Update OLED
    device.display(image)

    time.sleep(1)

# -------------------------------------------------
# Final Exit
# -------------------------------------------------

# Send final frame one last time
device.display(image)

print("OLED stopped. Last frame preserved.")

# EXIT NORMALLY
sys.exit(0)
