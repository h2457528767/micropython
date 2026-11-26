from machine import ADC
import time

names = {0: "P000", 1: "P001", 2: "P002", 4: "P004", 7: "P003", 11: "P013"}
adcs = {}
for ch in names:
    adcs[ch] = ADC(("adc0", ch))

while True:
    for ch in sorted(names):
        uv = adcs[ch].read_uv()
        print("%s (AN%03d): %.3f V" % (names[ch], ch, uv / 1000000), end=" ")
    print("\r\n")
    time.sleep_ms(100)
