from machine import ADC, Pin
import time

# 两点校准参数
ADC_GND = 2240
ADC_3V3 = 4393
VOLT_MAX = 3.3
k = VOLT_MAX / (ADC_3V3 - ADC_GND)

adc = ADC(Pin(45))
adc.atten(ADC.ATTN_11DB)

while True:
    val = adc.read()
    # 线性换算
    vol = (val - ADC_GND) * k
    if vol < 0:
        vol = 0.0
    #print(f"ADC RAW:{val}, Voltage: {vol:.2f}V")
    print(f"ADC RAW:{val}")
    time.sleep(0.2)
