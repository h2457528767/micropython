# main.py —— INA219 电压/电流/功率（软件 I2C）
# INA219@0x40（A0/A1 跳线可改 0x41~0x4F）
import time
import gc
from machine import Pin, SoftI2C

# 软件 I2C：SCL=P100，SDA=P101（按你的板子改）
i2c = SoftI2C(scl=Pin("SCL"), sda=Pin("SDA"), freq=100000)

INA_ADDR = 0x40
SHUNT_OHM = 0.1          # 模块上的分流电阻，常见 0.1Ω（3.2A 量程）
MAX_CURRENT_A = 2.0      # 你预计的最大电流，用于算分辨率


# ==========================
# INA219
# ==========================
class INA219:
    REG_CONFIG = 0x00
    REG_SHUNT = 0x01
    REG_BUS = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CAL = 0x05

    # 32V FSR / PGA=±320mV / 12bit / 8 次平均 / 连续测量
    # bit15 RST=0, 14-13 BRNG=01(32V), 12-11 PG=11(±320mV),
    # 10-7 BADC=1001, 6-3 SADC=1001, 2-0 MODE=111
    CFG_DEFAULT = 0x399F

    def __init__(self, i2c, addr=INA_ADDR, shunt_ohm=SHUNT_OHM,
                 max_current_a=MAX_CURRENT_A):
        self._i2c = i2c
        self._addr = addr
        self._shunt = shunt_ohm
        self._current_lsb = 0.0
        self._power_lsb = 0.0
        time.sleep_ms(20)

        # 软复位，确保寄存器回到已知状态
        self._wr16(self.REG_CONFIG, 0x8000)
        time.sleep_ms(20)
        self._wr16(self.REG_CONFIG, self.CFG_DEFAULT)
        time.sleep_ms(20)

        self.set_calibration(shunt_ohm, max_current_a)

    # ---------- 底层 ----------
    def _rd16(self, reg):
        self._i2c.writeto(self._addr, bytes([reg]))
        d = self._i2c.readfrom(self._addr, 2)
        return (d[0] << 8) | d[1]          # INA219 是大端

    def _wr16(self, reg, val):
        self._i2c.writeto(self._addr,
                          bytes([reg, (val >> 8) & 0xFF, val & 0xFF]))

    @staticmethod
    def _s16(v):
        return v - 65536 if v > 32767 else v

    # ---------- 校准 ----------
    def set_calibration(self, shunt_ohm, max_current_a):
        """按分流电阻和最大电流算 Current_LSB 并写校准寄存器"""
        self._shunt = shunt_ohm
        # Current_LSB 取 max/32768，向上取整到 100µA 更方便读数
        lsb = max_current_a / 32768.0
        # 规整到 1/2/5 × 10^n 附近的常用值
        for cand in (0.00001, 0.00002, 0.00005, 0.0001, 0.0002,
                     0.0005, 0.001, 0.002, 0.005, 0.01):
            if cand >= lsb:
                lsb = cand
                break

        cal = int(0.04096 / (lsb * shunt_ohm))
        if cal <= 0 or cal > 65535:
            raise RuntimeError("校准值越界 cal=%d，检查分流电阻/量程" % cal)

        self._current_lsb = lsb
        self._power_lsb = 20.0 * lsb
        self._wr16(self.REG_CAL, cal)
        time.sleep_ms(5)
        return cal

    # ---------- 读取 ----------
    def bus_voltage(self):
        """总线电压 V（0~32V）"""
        raw = self._rd16(self.REG_BUS)
        if raw & 0x01:                      # bit0 = OVF，量程溢出
            raise RuntimeError("总线电压溢出（>32V）")
        return (raw >> 3) * 0.004           # LSB = 4mV

    def shunt_voltage(self):
        """分流电压 mV（±320mV），有符号"""
        return self._s16(self._rd16(self.REG_SHUNT)) * 0.01   # LSB = 10µV

    def current(self):
        """电流 A，有符号"""
        return self._s16(self._rd16(self.REG_CURRENT)) * self._current_lsb

    def power(self):
        """功率 W"""
        return self._rd16(self.REG_POWER) * self._power_lsb

    def read(self):
        """返回 (总线电压V, 分流mV, 电流A, 功率W)"""
        v = self.bus_voltage()
        sv = self.shunt_voltage()
        i = self.current()
        p = self.power()
        return v, sv, i, p

    def config(self):
        return self._rd16(self.REG_CONFIG)


# =============================
# 主程序
# =============================
def main():
    gc.collect()
    found = i2c.scan()
    print("I2C scan:", [hex(a) for a in found])

    if INA_ADDR not in found:
        print("未找到 INA219 (0x%02X)，检查接线/地址跳线" % INA_ADDR)
        return

    try:
        ina = INA219(i2c)
        print("INA219 OK, config=0x%04X, current_lsb=%.6fA"
              % (ina.config(), ina._current_lsb))
    except Exception as e:
        print("INA219 初始化失败:", e)
        return

    n = 0
    while True:
        try:
            v, sv, i, p = ina.read()
            print("Bus=%.3fV  Shunt=%.2fmV  I=%.1fmA  P=%.1fmW"
                  % (v, sv, i * 1000.0, p * 1000.0))
        except Exception as e:
            print("INA219 err:", e)

        n += 1
        if n % 30 == 0:
            gc.collect()
        time.sleep(1)


main()
