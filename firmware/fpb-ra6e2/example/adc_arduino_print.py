# 扫描 Arduino J6 上的 A0..A5（RA6E2 ADC0，12 bit，VREFH0=3.3 V）。
# machine.ADC 只接受 (设备名, AN 通道) 元组，通道必须先在设备树 zephyr,user 里列出。
from machine import ADC
import time

# A0..A5 -> (adc0, ANxxx)，见 docs/pinout.md
CHANNELS = [
    ("A0", 0),    # P000 AN000
    ("A1", 1),    # P001 AN001
    ("A2", 2),    # P002 AN002
    ("A3", 4),    # P004 AN004
    ("A4", 7),    # P003 AN007
    ("A5", 11),   # P013 AN011
]

adcs = [(name, ADC(("adc0", ch))) for name, ch in CHANNELS]

VREF_MV = 3300

while True:
    line = []
    for name, adc in adcs:
        raw = adc.read_u16()            # 已按分辨率线性放大到 16 bit
        mv = raw * VREF_MV // 65536
        line.append("%s=%4d mV" % (name, mv))
    print("  ".join(line))
    time.sleep_ms(500)
