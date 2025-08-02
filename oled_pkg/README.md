# TITAN OLED PACKAGE:

Refer to requirements.txt for necessary dependencies

## Hardware Connection:

SDA ==> GPIO 2(pin 3)
SCL ==> GPIO 3(pin 5)
VCC ==> 3.3V(pin 1) OR 5V(pin 2 or 4)
GND ==> GND(pin 6)


In terminal:

```sudo raspi-config```


Select interfacing options->I2C option->Yes and Ok->Finish

```sudo reboot```

```sudo i2cdetect -y 1```

This should show something like 

     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --          


**For RPI 4:**

To install Adafruit libraries

```
git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
git clone https://github.com/adafruit/Adafruit_Python_SSD1306.git

cd Adafruit_Python_GPIO
sudo python3 setup.py install

cd ..
cd Adafruit_Python_SSD1306
sudo python3 setup.py install
```

**For RPI 5:**

If pip error:

```
pip3 install --break-system-packages RPi.GPIO
pip3 install --break-system-packages Adafruit-SSD1306 smbus2 pillow
```

Finally you can run it using:

```python3 oled_ip_pix.py   #replace x with pi name```
