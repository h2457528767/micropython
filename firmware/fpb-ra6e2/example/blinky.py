from machine import Pin
import time

#led1 = Pin("P207", Pin.OUT)   # LED1
#led2 = Pin("P206", Pin.OUT)   # LED2

led1 = Pin("LED1", Pin.OUT)
led2 = Pin("LED2", Pin.OUT)

while True:
    led1.value(1)
    led2.value(0)
    time.sleep_ms(250)
    led1.value(0)
    led2.value(1)
    time.sleep_ms(250)
