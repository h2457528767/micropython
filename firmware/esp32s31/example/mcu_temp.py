import esp32
import time

try:
    while True:
        temp = esp32.mcu_temperature()
        print(f"mcu: {temp:.1f}°C")
        time.sleep(1)
except KeyboardInterrupt:
    print('Stop Print.')
finally:
    print('Terminate Program.')
