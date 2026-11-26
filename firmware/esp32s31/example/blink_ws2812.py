from machine import Pin
import neopixel
import time

PIN_NUM = 60
LED_COUNT = 1
np = neopixel.NeoPixel(Pin(PIN_NUM), LED_COUNT)

bright = 0.01  # 亮度系数 0~1

def set_bright_color(r,g,b):
    nr = int(r * bright)
    ng = int(g * bright)
    nb = int(b * bright)
    np[0] = (nr, ng, nb)
    np.write()

while True:
    set_bright_color(255,255,255)
    time.sleep_ms(500)
    set_bright_color(0,0,0)
    time.sleep_ms(500)
