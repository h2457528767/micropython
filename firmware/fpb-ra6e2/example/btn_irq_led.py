from machine import Pin
from time import sleep_ms

leds = [
    Pin("LED1", Pin.OUT),      # P207
    Pin("LED2", Pin.OUT),      # P206
]
btn = Pin("SW1", Pin.IN, Pin.PULL_UP)   # P304 按下为 0

speeds = [300, 200, 100, 50]            # 每档流水间隔 ms
idx = 0
flag = False                           # 中断置位标志

def on_press(pin):
    """中断服务标志"""
    global flag
    flag = True

btn.irq(trigger=Pin.IRQ_FALLING, handler=on_press)   # 下降沿 = 按下

pos = 0
print("速度档位", idx, "间隔", speeds[idx], "ms")

while True:
    # ---- 处理按键事件 ----
    if flag:
        flag = False
        idx = (idx + 1) % len(speeds)
        print("速度档位", idx, "间隔", speeds[idx], "ms")

    # ---- 流水一步 ----
    for i, led in enumerate(leds):
        led.value(1 if i == pos else 0)
    pos = (pos + 1) % len(leds)

    sleep_ms(speeds[idx])
