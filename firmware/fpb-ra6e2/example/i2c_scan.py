# https://docs.micropython.org/en/v1.29.0/zephyr/quickref.html
from machine import I2C

i2c = I2C("i2c", freq=100000)   # construct an i2c bus # P100=SCL P101=SDA
print(i2c)   # print device name

addrs = i2c.scan()    # scan the device for available I2C slaves

print("扫到地址:", [hex(a) for a in addrs])