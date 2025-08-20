#!/usr/bin/env python3

import time
import subprocess
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

#pin configuration:
RST = None  # For I2C, RST is not used

# Initialize display (128x32 OLED via I2C)
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
disp.begin()
disp.clear()
disp.display()

# Image buffer
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Font and layout
font = ImageFont.load_default()
padding = -2
top = padding
x = 0

while True:
    # Clear image
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Get Wi-Fi SSID
    try:
        cmd = "iwgetid -r"
        WifiSSID = subprocess.check_output(cmd, shell=True).decode("utf-8").strip().upper()
        if not WifiSSID:
            WifiSSID = "NO NETWORK"
        Network = "WIFI: " + WifiSSID
    except:
        Network = "WIFI: NO NETWORK"

    # Get IP address
    try:
        cmd = "hostname -I | cut -d' ' -f1"
        ip_raw = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        IP = "IP: " + (ip_raw.upper() if ip_raw else "NO IP")
    except:
        IP = "IP: NO IP"

    # Get memory usage
    cmd = "free -m | awk 'NR==2{printf \"MEM: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8").strip().upper()

    # Get CPU load + % usage
    try:
        cmd = "top -bn1 | grep '%Cpu(s)' | awk '{print 100 - $8}'"
        cpu_percent = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        cmd = "top -bn1 | grep load | awk '{printf \"CPU LOAD: %.2f (%s%%)\", $(NF-2), \"" + cpu_percent + "\"}'"
        CPU = subprocess.check_output(cmd, shell=True).decode("utf-8").strip().upper()
    except:
        CPU = "CPU LOAD: N/A"

    # Get disk usage (optional)
    # cmd = "df -h | awk '$NF==\"/\"{printf \"DISK: %d/%dGB %s\", $3,$2,$5}'"
    # Disk = subprocess.check_output(cmd, shell=True).decode("utf-8").strip().upper()

    # Draw system info
    draw.text((x, top),         Network,   font=font, fill=255)
    draw.text((x, top + 8),     IP,        font=font, fill=255)
    draw.text((x, top + 16),    MemUsage,  font=font, fill=255)
    draw.text((x, top + 25),    CPU,       font=font, fill=255)
    # draw.text((x, top + 25),    Disk,     font=font, fill=255)  # Uncomment to show disk space

    # Display image
    disp.image(image)
    disp.display()
    time.sleep(1)
