import time
import subprocess
import smbus2
import warnings
from pathlib import Path

# Suppress Adafruit GPIO escape sequence warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import Adafruit_SSD1306
import Adafruit_GPIO.Platform as Platform
from PIL import Image, ImageDraw, ImageFont

# --- Force platform to Raspberry Pi ---
Platform.platform_detect = lambda: Platform.RASPBERRY_PI

# --- OLED display setup ---
RST = None  # For I2C, RST is not used
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
disp.begin()
disp.clear()
disp.display()

# --- Create image buffer ---
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# --- Font and layout ---
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not Path(font_path).exists():
    raise FileNotFoundError(f"Font not found at {font_path}")

font = ImageFont.truetype(font_path, size=8)
padding = -2
top = padding
x = 0

try:
    while True:
        # Clear image
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # Get Wi-Fi SSID
        try:
            cmd = "iwgetid -r"
            WifiSSID = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip().upper()
            if not WifiSSID:
                WifiSSID = "NO NETWORK"
            Network = "WIFI: " + WifiSSID
        except Exception:
            Network = "WIFI: NO NETWORK"

        # Get IP address
        try:
            cmd = "hostname -I | cut -d' ' -f1"
            ip_raw = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
            IP = "IP: " + (ip_raw.upper() if ip_raw else "NO IP")
        except Exception:
            IP = "IP: NO IP"

        # Get memory usage
        try:
            cmd = "free -m | awk 'NR==2{printf \"MEM: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
            MemUsage = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip().upper()
        except Exception:
            MemUsage = "MEM: N/A"

        # Get CPU load
        try:
            cmd = "top -bn1 | grep '%Cpu(s)' | awk '{print 100 - $8}'"
            cpu_percent = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
            cmd = f"top -bn1 | grep load | awk '{{printf \"CPU LOAD: %.2f (%s%%)\", $(NF-2), \"{cpu_percent}\"}}'"
            CPU = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip().upper()
        except Exception:
            CPU = "CPU LOAD: N/A"

        # Draw system info
        draw.text((x, top),         Network,   font=font, fill=255)
        draw.text((x, top + 8),     IP,        font=font, fill=255)
        draw.text((x, top + 16),    MemUsage,  font=font, fill=255)
        draw.text((x, top + 24),    CPU,       font=font, fill=255)

        # Display image
        disp.image(image)
        disp.display()
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[INFO] Script interrupted. Clearing display...")

finally:
    # Clear the display before exiting
    disp.clear()
    disp.display()
    print("[INFO] OLED display turned off. Exiting.")
