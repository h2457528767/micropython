from machine import ADC, Pin
import time

adc = ADC(Pin(45)) # 声明ADC对象 设置D34号引脚作为ADC采样引脚
adc.atten(ADC.ATTN_11DB) # 设置衰减比 满量程3.3v

while True:
    val = adc.read()
    vol = val/4095*3.3
    print("ADC RAW: %d, Voltage: %.2fV" %(val, vol))
    time.sleep(1)