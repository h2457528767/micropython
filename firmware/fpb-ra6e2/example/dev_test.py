from machine import SoftI2C, SPI, PWM, Pin, ADC, UART

# 1) SoftI2C —— 设备名字符串
scl = Pin("SCL", Pin.OUT)
sda = Pin("SDA", Pin.OUT)
try:
    i2c = SoftI2C(scl=scl, sda=sda, freq=100000)
    print("I2C init OK, scan:", i2c.scan())
except Exception as e:
    print("I2C fail:", repr(e))

# 2) SPI
try:
    spi = SPI("spi0", baudrate=1000000)
    print("SPI init OK:", spi)
except Exception as e:
    print("SPI fail:", repr(e))

# 3) PWM —— PA5 绿灯，通道0
try:
    p = PWM(("pwm1", 0), freq=1000, duty_u16=32768)
    p.freq(1000)
    p.duty_u16(32768)
    print("PWM OK")
except Exception as e:
    print("PWM fail:", repr(e))

# 4) ADC —— 通道0
try:
    a = ADC(("adc0", 0));
    print("ADC OK:", a.read_u16())
except Exception as e:
    print("ADC fail:", repr(e))
