# Arduino CLI

Arduino-cli is the official command-line interface that does exactly the same as Arduino IDE

-> Parses .ino sketches

-> Resolves libraries/dependencies

-> Compiles to machine code using GCC ARM toolchain

-> Calls esptool.py to flash via ROM bootloader over USB serial

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
echo 'export PATH="$PATH:/home/titan/bin"' >> ~/.bashrc
source ~/.bashrc
```

## Setup

1. Create a config file
```bash
arduino-cli config init
```

2. Set connection timeout to 600 seconds
```bash
arduino-cli config set network.connection_timeout 600s
```

3. Core installation
```bash
arduino-cli core update-index
arduino-cli core install esp32:esp32
```

## Check Board and Port

```bash
arduino-cli board list
```

You will see something like
```bash
Port         Protocol Type              Board Name FQBN Core
/dev/ttyAMA0 serial   Serial Port       Unknown
/dev/ttyUSB0 serial   Serial Port (USB) Unknown
/dev/ttyUSB1 serial   Serial Port (USB) Unknown
```

If you don't see FQBN,
1) For a generic board, FQBN=esp32:esp32:esp32
2) For ESP32S3, FQBN=esp32:esp32:esp32s3

Based on your board,
```bash
FQBN=esp32:esp32:esp32
echo $FQBN
# should print esp32:esp32:esp32  or  esp32:esp32:esp32s3
```

## Compile the code

```bash
cd /path/to/sketch/folder
arduino-cli compile --fqbn $FQBN .
```

Should show an output like
```bash
Sketch uses 316907 bytes (24%) of program storage space. Maximum is 1310720 bytes.
Global variables use 21544 bytes (6%) of dynamic memory, leaving 306136 bytes for local variables. Maximum is 327680 bytes.
```

## Upload the code




## Troubleshooting
1. If you get this error while uploading
```bash
Usage: esptool [OPTIONS] COMMAND [ARGS]...

Try 'esptool -h' for help
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Invalid value for '--port' / '-p': Path '/dev/ttyUSB1' is not readable. │
╰──────────────────────────────────────────────────────────────────────────────╯

Failed uploading: uploading error: exit status 2
```

Check permissions and groups
```bash
ls -l /dev/ttyUSB*
groups
```
You’ll likely see crw-rw---- root dialout /dev/ttyUSB1 and your user not yet in dialout

Add your user to the dialout
```bash
sudo usermod -aG dialout,tty titan
```

And reboot
```bash
sudo reboot
```

2. If you get an esptool error like
```bash
Traceback (most recent call last):
  File "esptool/__init__.py", line 1173, in _main
  File "esptool/__init__.py", line 1032, in main
  File "esptool/cli_util.py", line 229, in __call__
  File "rich_click/rich_command.py", line 404, in __call__
  File "click/core.py", line 1442, in __call__
  File "rich_click/rich_command.py", line 187, in main
  File "click/core.py", line 1830, in invoke
  File "click/core.py", line 1226, in invoke
  File "click/core.py", line 794, in invoke
  File "click/decorators.py", line 34, in new_func
  File "esptool/__init__.py", line 688, in write_flash_cli
  File "esptool/cmds.py", line 1112, in attach_flash
  File "esptool/loader.py", line 1091, in flash_id
  File "esptool/loader.py", line 1653, in run_spiflash_command
  File "esptool/loader.py", line 901, in read_reg
  File "esptool/loader.py", line 565, in check_command
  File "esptool/loader.py", line 495, in command
  File "esptool/loader.py", line 431, in read
StopIteration

A fatal error occurred: The chip stopped responding.
Stub flasher running.
```

Then add explicit upload flags so esptool uses a safer baudrate (e.g., 115200 or 230400)
```bash
arduino-cli upload -p /dev/ttyUSB0 --fqbn $FQBN --upload-property upload.speed=115200 .
```

