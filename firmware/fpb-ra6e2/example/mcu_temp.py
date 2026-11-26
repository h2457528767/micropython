import zsensor, time

t = zsensor.Sensor("dietemp")
while True:
    t.measure()
    temp = t.get_float(zsensor.DIE_TEMP)
    print("MCU temperature: %.1f C" % temp)
    time.sleep(1)
