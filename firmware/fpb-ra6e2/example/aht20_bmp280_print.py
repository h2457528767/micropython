# main.py —— AHT20 温湿度 + BMP280 气压/海拔
# AHT20@0x38   BMP280@0x77
import time
from machine import SoftI2C

# 1) 打开总线上下拉
pu_scl = Pin("P400", Pin.OUT)
pu_sda = Pin("P401", Pin.OUT)
pu_scl.value(1)
pu_sda.value(1)

# 2) 总线：Uno 脚位 SCL=P100，SDA=P101
scl = Pin("SCL", Pin.OUT)
sda = Pin("SDA", Pin.OUT)
i2c = SoftI2C(scl=scl, sda=sda, freq=100000)

AHT_ADDR = 0x38
BMP_ADDR = 0x77
SEA_LEVEL_PA = 101325.0


# =====================
# AHT20
# =====================
class AHT20:
    CMD_INIT = 0xBE
    CMD_TRIGGER = 0xAC
    CMD_RESET = 0xBA
    ST_BUSY = 0x80
    ST_CAL = 0x08

    def __init__(self, i2c, addr=AHT_ADDR):
        self._i2c = i2c
        self._addr = addr
        time.sleep_ms(100)
        self.reset()
        if not self.initialize():
            raise RuntimeError("AHT20 初始化失败, status=0x%02X" % self.status)

    def reset(self):
        self._i2c.writeto(self._addr, bytes([self.CMD_RESET]))
        time.sleep_ms(30)

    def initialize(self):
        self._i2c.writeto(self._addr, bytes([self.CMD_INIT, 0x08, 0x00]))
        time.sleep_ms(20)
        try:
            self._wait_idle()
        except RuntimeError:
            return False
        return bool(self.status & self.ST_CAL)

    @property
    def status(self):
        return self._i2c.readfrom(self._addr, 1)[0]

    def _wait_idle(self, timeout_ms=500):
        dl = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self.status & self.ST_BUSY:
            if time.ticks_diff(time.ticks_ms(), dl) > 0:
                raise RuntimeError("AHT20 busy timeout")
            time.sleep_ms(5)

    def read(self):
        self._i2c.writeto(self._addr, bytes([self.CMD_TRIGGER, 0x33, 0x00]))
        time.sleep_ms(80)
        self._wait_idle()
        d = self._i2c.readfrom(self._addr, 7)
        if d[0] & self.ST_BUSY:
            raise RuntimeError("AHT20 still busy, st=0x%02X" % d[0])
        h = ((d[1] << 12) | (d[2] << 4) | (d[3] >> 4)) * 100.0 / (1 << 20)
        raw_t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
        t = raw_t * 200.0 / (1 << 20) - 50.0
        return t, h


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
    MODE_NORMAL = 0x57
    MODE_FORCED = 0x55       # temp x2, press x16, forced

    def __init__(self, i2c, addr=BMP_ADDR):
        self._i2c = i2c
        self._addr = addr
        self._t_fine = 0
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
        v1 = (((adc_t >> 3) - (self._T1 << 1)) * self._T2) >> 11
        v2 = (((((adc_t >> 4) - self._T1) * ((adc_t >> 4) - self._T1)) >> 12)
              * self._T3) >> 14
        self._t_fine = v1 + v2
        t = ((self._t_fine * 5 + 128) >> 8) / 100.0

        # --- 气压 ---
        v1 = self._t_fine - 128000
        v2 = v1 * v1 * self._P6
        v2 = v2 + ((v1 * self._P5) << 17)
        v2 = v2 + (self._P4 << 35)
        v1 = ((v1 * v1 * self._P3) >> 8) + ((v1 * self._P2) << 12)
        v1 = (((1 << 47) + v1) * self._P1) >> 33
        if v1 == 0:
            p_pa = 0.0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - v2) * 3125) // v1
            v1b = (self._P9 * (p >> 13) * (p >> 13)) >> 25
            v2b = (self._P8 * p) >> 19
            p = ((p + v1b + v2b) >> 8) + (self._P7 << 4)
            p_pa = p / 256.0

        return t, p_pa, self._altitude(p_pa)

    @staticmethod
    def _altitude(p_pa, p0=SEA_LEVEL_PA):
        if p_pa <= 0:
            return 0.0
        return 44330.0 * (1.0 - (p_pa / p0) ** 0.190295)


# =============================
# 主程序
# =============================
def main():
    found = i2c.scan()
    print("I2C scan:", [hex(a) for a in found])

    aht = bmp = None

    if AHT_ADDR in found:
        try:
            aht = AHT20(i2c)
            print("AHT20 OK, status=0x%02X" % aht.status)
        except Exception as e:
            print("AHT20 初始化失败:", e)
    else:
        print("未找到 AHT20 (0x38)")

    if BMP_ADDR in found:
        try:
            bmp = BMP280(i2c)
            print("BMP OK, chip_id=0x%02X, T1=%d P1=%d"
                  % (bmp.chip_id, bmp._T1, bmp._P1))
        except Exception as e:
            print("BMP280 初始化失败:", e)
    else:
        print("未找到气压计 (0x77)")

    if aht is None and bmp is None:
        print("传感器不可用，退出")
        return

    while True:
        line = []
        if aht is not None:
            try:
                t, h = aht.read()
                line.append("T=%.2fC RH=%.2f%%" % (t, h))
            except Exception as e:
                line.append("AHT err:%s" % e)
        if bmp is not None:
            try:
                t2, p, alt = bmp.read()
                line.append("P=%.2fhPa Alt=%.1fm (BMP T=%.2fC)"
                            % (p / 100.0, alt, t2))
            except Exception as e:
                line.append("BMP err:%s" % e)
        print("  ".join(line))
        time.sleep(2)


main()

