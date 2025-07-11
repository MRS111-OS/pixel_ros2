import time
import subprocess

def toggle_wifi(state):
    if state == "on":
        subprocess.run(["nmcli", "radio", "wifi", "on"])
    elif state == "off":
        subprocess.run(["nmcli", "radio", "wifi", "off"])

def main():
    print("Waiting for input from /dev/rfcomm0...")
    with open("/dev/rfcomm0", "r+b", buffering=0) as rfcomm:
        while True:
            line = rfcomm.readline().decode().strip()
            print(f"Received: {line}")
            if line == "WIFI_ON":
                toggle_wifi("on")
                rfcomm.write(b"OK\n")
            elif line == "WIFI_OFF":
                toggle_wifi("off")
                rfcomm.write(b"OK\n")
            elif line == "BYE":
                rfcomm.write(b"BYE\n")
                break
            else:
                rfcomm.write(b"UNKNOWN\n")

if __name__ == "__main__":
    main()
