# main.py —— BMP280 气压/温度/海拔（软件 I2C）
# BMP280 @0x77
import time
import gc
from machine import Pin, SoftI2C

# 软件 I2C：SCL=P100，SDA=P101
scl = Pin("SCL", Pin.OUT)
sda = Pin("SDA", Pin.OUT)
i2c = SoftI2C(scl=scl, sda=sda, freq=100000)

BMP_ADDR = 0x77
SEA_LEVEL_PA = 101325.0

Alt_Shift = +1200

# ==========================
# BMP280
# ==========================
class BMP280:
    REG_ID = 0xD0
    REG_RESET = 0xE0
    REG_STATUS = 0xF3
    REG_CTRL = 0xF4
    REG_CONFIG = 0xF5
    REG_DATA = 0xF7

    CFG_CONFIG = 0x2C        # IIR x4, standby 62.5ms
    CFG_CTRL = 0x57          # temp x2, press x16, normal

    def __init__(self, i2c, addr=BMP_ADDR):
        self._i2c = i2c
        self._addr = addr
        self._t_fine = 0.0
        time.sleep_ms(10)

        cid = self._rd(self.REG_ID, 1)[0]
        if cid not in (0x58, 0x60):
            raise RuntimeError("chip_id=0x%02X 不是 BMP280/BME280" % cid)
        self.chip_id = cid

        self._soft_reset()
        self._load_calib()
        self._configure()

    # ---------- 底层：split 读写，不用 *_mem ----------
    def _rd(self, reg, n):
        self._i2c.writeto(self._addr, bytes([reg]))
        return self._i2c.readfrom(self._addr, n)

    def _wr(self, reg, val):
        self._i2c.writeto(self._addr, bytes([reg, val & 0xFF]))

    @staticmethod
    def _s16(v):
        return v - 65536 if v > 32767 else v

    def _soft_reset(self):
        self._wr(self.REG_RESET, 0xB6)
        time.sleep_ms(10)
        for _ in range(50):                     # 等 im_update 清零
            if not (self._rd(self.REG_STATUS, 1)[0] & 0x01):
                break
            time.sleep_ms(2)

    def _load_calib(self):
        d = self._rd(0x88, 24)
        self._T1 = d[0] | (d[1] << 8)
        self._T2 = self._s16(d[2] | (d[3] << 8))
        self._T3 = self._s16(d[4] | (d[5] << 8))
        self._P1 = d[6] | (d[7] << 8)
        self._P2 = self._s16(d[8] | (d[9] << 8))
        self._P3 = self._s16(d[10] | (d[11] << 8))
        self._P4 = self._s16(d[12] | (d[13] << 8))
        self._P5 = self._s16(d[14] | (d[15] << 8))
        self._P6 = self._s16(d[16] | (d[17] << 8))
        self._P7 = self._s16(d[18] | (d[19] << 8))
        self._P8 = self._s16(d[20] | (d[21] << 8))
        self._P9 = self._s16(d[22] | (d[23] << 8))

        # 合理性检查：T1 约 27000~28000，P1 约 36000~37000
        if self._T1 in (0, 0xFFFF) or self._P1 in (0, 0xFFFF):
            raise RuntimeError("校准参数异常 T1=%d P1=%d，I2C 读寄存器有问题"
                               % (self._T1, self._P1))

    def _configure(self):
        self._wr(self.REG_CONFIG, self.CFG_CONFIG)
        self._wr(self.REG_CTRL, self.CFG_CTRL)
        time.sleep_ms(60)
        got = self._rd(self.REG_CTRL, 1)[0]
        if got != self.CFG_CTRL:
            raise RuntimeError("CTRL 写入失败: 期望 0x%02X 实际 0x%02X"
                               % (self.CFG_CTRL, got))

    # ---------- 读取 ----------
    def _wait_ready(self, timeout_ms=200):
        dl = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self._rd(self.REG_STATUS, 1)[0] & 0x08:      # measuring
            if time.ticks_diff(time.ticks_ms(), dl) > 0:
                raise RuntimeError("BMP280 measure timeout")
            time.sleep_ms(2)

    def read(self):
        """返回 (温度°C, 气压Pa, 海拔m)"""
        self._wait_ready()
        d = self._rd(self.REG_DATA, 6)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)

        # --- 温度 ---
        var1 = (adc_t / 16384.0 - self._T1 / 1024.0) * self._T2
        var2 = (adc_t / 131072.0 - self._T1 / 8192.0)
        var2 = var2 * var2 * self._T3
        self._t_fine = var1 + var2
        t = self._t_fine / 5120.0

        # --- 气压 ---
        var1 = (self._t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self._P6 / 32768.0
        var2 = var2 + var1 * self._P5 * 2.0
        var2 = (var2 / 4.0) + (self._P4 * 65536.0)
        var1 = (self._P3 * var1 * var1 / 524288.0 + self._P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._P1
        if var1 == 0:
            p_pa = 0.0
        else:
            p = 1048576.0 - adc_p
            p = (p - (var2 / 4096.0)) * 6250.0 / var1
            var1 = self._P9 * p * p / 2147483648.0
            var2 = p * self._P8 / 32768.0
            p_pa = p + (var1 + var2 + self._P7) / 16.0

        return t, p_pa, self._altitude(p_pa)

    @staticmethod
    def _altitude(p_pa, p0=SEA_LEVEL_PA + Alt_Shift):
        if p_pa <= 0:
            return 0.0
        return 44330.0 * (1.0 - (p_pa / p0) ** 0.190295)


# =============================
# 主程序
# =============================
def main():
    gc.collect()
    print("free before:", gc.mem_free())

    found = i2c.scan()
    print("I2C scan:", [hex(a) for a in found])

    if BMP_ADDR not in found:
        print("未找到气压计 (0x77)，退出")
        return

    try:
        bmp = BMP280(i2c)
        print("BMP OK, chip_id=0x%02X, T1=%d P1=%d"
              % (bmp.chip_id, bmp._T1, bmp._P1))
    except Exception as e:
        print("BMP280 初始化失败:", e)
        return

    gc.collect()
    print("free after init:", gc.mem_free())

    n = 0
    while True:
        try:
            t, p, alt = bmp.read()
            print("P = %.2f hPa  Alt = %.1f m  T = %.2f C" % (p / 100.0, alt, t))
        except Exception as e:
            print("BMP err:", e)

        n += 1
        if n % 30 == 0:          # 每 60 秒回收一次
            gc.collect()

        time.sleep(1)


main()
