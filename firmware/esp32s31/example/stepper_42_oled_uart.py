from machine import Pin, I2C, UART
from ssd1306 import SSD1306_I2C
import time
import ujson

# ==== Define hardware pinout =====
dir_pin = Pin(36, Pin.OUT)
step_pin = Pin(37, Pin.OUT)
en_pin = Pin(38, Pin.OUT)

# Initialize OLED I2C
i2c = I2C(0, scl=Pin(47), sda=Pin(48))
oled = SSD1306_I2C(128, 64, i2c)

# Initialize UART 
uart = UART(1, baudrate=115200, tx=Pin(2), rx=Pin(3))

# ======== Angle Calculation ==========
step_angle = 1.8 # 步距角
step_cycle = 360 / 1.8 # 360 / 1.8 = 200 步/圈
# microstep mode, default is 1/8 so 8
# another ex: 1/16 microstep would be 16
microMode = 8
# full rotation multiplied by the microstep divider
steps = step_cycle * microMode  # 200 * 8细分 = 1600 脉冲/圈
# 1600 / 360 = 4.444444 脉冲/度
STEPS_PER_DEGREE = steps / 360

# ======== OLED Display ===========
def display_motor(status="READY", angle=0.0, speed=1200, dir_str="STOP"):
    oled.fill(0)
    oled.text("==== MOTOR ====", 0, 0)
    oled.text(f"Status: {status}", 0, 15)
    oled.text(f"Angle: {angle:.1f} deg", 0, 27)
    oled.text(f"Direction: {dir_str}", 0, 39)
    oled.text(f"Speed: {speed}us", 0, 51)
    oled.rotate(1)
    oled.show()

# ======= Motor Control =========
def rotate_angle(angle, speed_us):
    en_pin.value(0)
    dir_pin.value(angle > 0)   # Rotate direction
    dir_str = "CW" if angle > 0 else "CCW"
    
    display_motor("RUN", angle, speed_us, dir_str)  # rotate direction display
    target_angle = abs(angle)
    total_steps = int(target_angle * STEPS_PER_DEGREE)  # rotate steps
    
    # Start rotate
    for _ in range(total_steps):
        step_pin.value(1)
        time.sleep_us(speed_us)
        step_pin.value(0)
        time.sleep_us(speed_us)
    print("Rotate %.1f degree i.e. %d steps" % (angle, total_steps))
    release()
    display_motor("STOP", angle, speed_us, dir_str)

def release():
    en_pin.value(1)

# ======== UART Control =========
def uart_control():
    while True:
        if uart.any():
            cmd = uart.read()
            try:
                data = ujson.loads(cmd)
                angle = float(data['angle'])
                speed = int(data.get('speed', 1200))
                
                rotate_angle(angle, speed)
                uart.write('OK\r\n')
                
            except:
                uart.write('Invalid command\r\n')
                release()
        else:
            release()
            time.sleep_ms(50)

# ======== main ==========
display_motor()
while True:
    uart_control()
