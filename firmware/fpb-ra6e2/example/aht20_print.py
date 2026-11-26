# main.py —— AHT20 温湿度传感器
import time
from machine import Pin, SoftI2C


# ============================================================
# 驱动部分
# ============================================================
class AHT10:
    """AHT10/AHT20 温湿度驱动（纯读方式）"""

    AHTX0_I2CADDR_DEFAULT = 0x38
    AHTX0_CMD_INITIALIZE = 0xE1      # AHT10 用 0xE1
    AHTX0_CMD_TRIGGER = 0xAC
    AHTX0_CMD_SOFTRESET = 0xBA
    AHTX0_STATUS_BUSY = 0x80
    AHTX0_STATUS_CALIBRATED = 0x08

    def __init__(self, i2c, address=AHTX0_I2CADDR_DEFAULT):
        self._i2c = i2c
        self._address = address
        self._temp = None
        self._humidity = None
        time.sleep_ms(100)           # 上电/软重启后稳定
        self.reset()
        if not self.initialize():
            raise RuntimeError("AHT 初始化失败, status=0x%02X" % self.status)

    # ---------- 基础操作 ----------
    def reset(self):
        """软复位 0xBA，能把卡住的传感器救回来"""
        self._i2c.writeto(self._address, bytes([self.AHTX0_CMD_SOFTRESET]))
        time.sleep_ms(30)

    def initialize(self):
        """发初始化/校准命令，返回是否已校准"""
        self._i2c.writeto(self._address,
                          bytes([self.AHTX0_CMD_INITIALIZE, 0x08, 0x00]))
        time.sleep_ms(20)
        try:
            self._wait_for_idle()
        except RuntimeError:
            return False
        return bool(self.status & self.AHTX0_STATUS_CALIBRATED)

    @property
    def status(self):
        """纯读 1 字节状态，绝不能写'寄存器地址'"""
        return self._i2c.readfrom(self._address, 1)[0]

    def _wait_for_idle(self, timeout_ms=500):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self.status & self.AHTX0_STATUS_BUSY:
            if time.ticks_diff(time.ticks_ms(), deadline) > 0:
                raise RuntimeError("AHT busy timeout")
            time.sleep_ms(5)

    def _trigger(self):
        self._i2c.writeto(self._address,
                          bytes([self.AHTX0_CMD_TRIGGER, 0x33, 0x00]))

    # ---------- 读取 ----------
    def read(self):
        """一次测量，返回 (温度°C, 湿度%RH)"""
        self._trigger()
        time.sleep_ms(80)            # 典型 80ms，先固定等再轮询
        self._wait_for_idle()

        # 纯读 7 字节: status + 湿度20bit + 温度20bit + crc
        d = self._i2c.readfrom(self._address, 7)

        if d[0] & self.AHTX0_STATUS_BUSY:
            raise RuntimeError("still busy, status=0x%02X" % d[0])

        self._humidity = ((d[1] << 12) | (d[2] << 4) | (d[3] >> 4)) \
                         * 100.0 / (1 << 20)
        raw = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
        self._temp = raw * 200.0 / (1 << 20) - 50.0
        return self._temp, self._humidity


class AHT20(AHT10):
    AHTX0_CMD_INITIALIZE = 0xBE      # AHT20 用 0xBE（去掉 const）


# ============================================================
# 主程序
# ============================================================
scl = Pin("SCL", Pin.OUT)
sda = Pin("SDA", Pin.OUT)
i2c = SoftI2C(scl=scl, sda=sda, freq=100000)

def main():
    found = i2c.scan()
    print("I2C scan:", [hex(a) for a in found])

    if AHT10.AHTX0_I2CADDR_DEFAULT not in found:
        print("未找到 0x38，请检查接线 / 上拉 / 供电")
        return

    try:
        aht = AHT20(i2c)
    except RuntimeError as e:
        print("初始化失败:", e)
        return

    print("初始化成功, status = 0x%02X" % aht.status)   # 正常应为 0x18

    while True:
        try:
            t, h = aht.read()
            print("AHT20 温度 %.2f C  湿度 %.2f %%" % (t, h))
        except Exception as e:
            print("读取失败:", e)
        time.sleep(2)


main()
