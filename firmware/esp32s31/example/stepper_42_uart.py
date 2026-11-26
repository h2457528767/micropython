from machine import Pin, UART
import machine, time
import ujson

# ==== Define hardware pinout =====
dir_pin = Pin(36, Pin.OUT)
step_pin = Pin(37, Pin.OUT)
en_pin = Pin(38, Pin.OUT)

# Initialize UART 
uart = UART(1, baudrate=115200, tx=Pin(2), rx=Pin(3))

# ======== Angle Calculation ==========
step_angle = 1.8 # step angle
step_cycle = 360 / 1.8 # 360 / 1.8 = 200 步/圈
# microstep mode, default is 1/8 so 8
# another ex: 1/16 microstep would be 16
microMode = 8
# full rotation multiplied by the microstep divider
steps = step_cycle * microMode  # 200 * 8细分 = 1600 脉冲/圈
# 1600 / 360 = 4.444444 脉冲/度
STEPS_PER_DEGREE = steps / 360

# ======= Motor Control =========
def rotate_angle(angle, speed_us):
    en_pin.value(0)
    dir_pin.value(angle > 0)   # Rotate direction
    dir_str = "CW" if angle > 0 else "CCW"
    
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
while True:
    uart_control()