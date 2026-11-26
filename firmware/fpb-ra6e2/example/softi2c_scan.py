# Arduino J1 的 SDA(P101)/SCL(P100) 上跑软件 I2C，扫描总线上的 7bit 地址。
#
# 两点必须注意（都来自原理图 D019002_04 第 3 页）：
#   1) SCL0/SDA0 的 2K2 上拉由 P400、P401 供电，板上原话：
#      "For I2C operation, set P400 and P401 to outputs driven high (pullups enabled)"
#      -> 做 I2C 前必须把 P400/P401 设为输出高，否则总线没有上拉，扫描必然为空。
#   2) 硬件 I2C 没开：RA6E2 无 RIIC，这两个脚属于 I3C0，Zephyr v4.4 没有对应驱动
#      （详见 README「I2C 说明」），所以这里用 machine.SoftI2C。
from machine import Pin, SoftI2C

# 1) 打开总线上下拉
pu_scl = Pin("P400", Pin.OUT)
pu_sda = Pin("P401", Pin.OUT)
pu_scl.value(1)
pu_sda.value(1)

# 2) 总线：Uno 脚位 SCL=P100，SDA=P101
scl = Pin("SCL", Pin.OUT)
sda = Pin("SDA", Pin.OUT)
i2c = SoftI2C(scl=scl, sda=sda, freq=100000)

print("扫描中 …")
found = i2c.scan()
print("发现从机地址:", [hex(a) for a in found] if found else "无")

# 用法示例（把 0x3C 换成扫描到的地址）：
#   i2c.writeto(0x3C, b"\x00\x00")          # 写
#   data = i2c.readfrom(0x3C, 6)            # 读
#   i2c.writeto_mem(0x68, 0x0F, b"\x75")    # 写寄存器
#   i2c.readfrom_mem(0x68, 0x0F, 1)         # 读寄存器
