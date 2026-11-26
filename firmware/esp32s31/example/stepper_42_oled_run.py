from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Define TMC2209 pinout
dir = Pin(36, Pin.OUT)
step = Pin(37, Pin.OUT)
en = Pin(38, Pin.OUT)

# ==== Initialized IIC OLED ====
i2c = I2C(0, scl=Pin(47), sda=Pin(48))
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

# ==== OLED 显示电机状态函数 ====
def display_motor_status(status, direction, speed):
    oled.fill(0)  # 清屏
    oled.text("=== MOTOR ===", 0, 0)
    oled.text("Status: " + status, 0, 20)
    oled.text("Direction: " + direction, 0, 35)
    oled.text("Speed: " + speed, 0, 50)
    oled.rotate(1)
    oled.show()

while True:
    en.value(0) # enable stepper
    dir.value(not dir.value()) # switch direction
    dir_str = "CW" if dir.value() == 0 else "CCW"
    display_motor_status("RUNNING", dir_str, "1200us")
    for _ in range(800):  # 180 度对应步数
        step.value(1)
        time.sleep_us(1200)
        step.value(0)
        time.sleep_us(1200)
    en.value(1) # disable stepper
    display_motor_status("STOPPED", dir_str, "1200us")
    print("rotated! now reverse")
    time.sleep(1)
