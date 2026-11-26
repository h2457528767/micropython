# https://docs.micropython.org/en/v1.29.0/zephyr/quickref.html
from machine import ADC
import time

adc = ADC(("adc0", 0))   # P000 - AN000
#adc = ADC(("adc0", 1))   # P001 - AN001
#adc = ADC(("adc0", 2))   # P002 - AN002
#adc = ADC(("adc0", 4))   # P004 - AN004
#adc = ADC(("adc0", 7))   # P003 - AN007
#adc = ADC(("adc0", 11))   # P013 - AN011

while True:
    vol_uv = adc.read_uv()
    vol_v = vol_uv / 1_000_000   # V
    print("PA0 = {:.3f} V".format(vol_v))
    time.sleep(0.1)
