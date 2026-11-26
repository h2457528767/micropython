# Arduino 风格点灯：D13 = P111（J1-6，SCK 复用脚），板上 LED1/LED2 同时闪。
# 注意 D13 与 SPI / Pmod1 复用，见 docs/pinout.md。
from machine import Pin
from time import sleep_ms

led = Pin("D13", Pin.OUT)          # 等价写法：Pin(("ioport1", 11), Pin.OUT)
onboard1 = Pin("LED1", Pin.OUT)    # P207
onboard2 = Pin("LED2", Pin.OUT)    # P206
btn = Pin("SW1", Pin.IN, Pin.PULL_UP)   # P304，按下为 0

while True:
    led.value(not led.value())
    onboard1.value(led.value())
    onboard2.value(not led.value())
    print("D13=%d  SW1=%d" % (led.value(), btn.value()))
    sleep_ms(300)
