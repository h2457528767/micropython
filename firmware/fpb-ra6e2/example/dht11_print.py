from machine import Pin
import time

DHT_PIN = ("ioport1", 5)
MAXRETRY = 3

# 高电平宽度阈值(us):0 码 26~28us,1 码 70us,取 45us 居中,两侧余量最大
BIT1_THRESH_US = 45
TIMEOUT_US = 300


def _wait_level(io, level, timeout_us=TIMEOUT_US):
    """等引脚变成 level,返回等待耗时(us);超时返回 -1"""
    t0 = time.ticks_us()
    while io.value() != level:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return -1
    return time.ticks_diff(time.ticks_us(), t0)


def dht11_read(pin_num):
    """返回 (湿度%RH, 温度℃) 或 (None, 错误说明)"""
    data = [0] * 5

    # --- 主机起始信号:拉低 >18ms,再拉高 20-40us ---
    io = Pin(pin_num, Pin.OUT, value=0)
    time.sleep_ms(20)
    io.value(1)
    time.sleep_us(30)

    # --- 切换为输入,等传感器应答 ---
    io.init(Pin.IN, Pin.PULL_UP)

    err = None
    try:
        if _wait_level(io, 0) < 0:            # 等 ACK 拉低
            err = 'no ack (check wiring/pullup)'
        elif _wait_level(io, 1) < 0:          # ACK 低 ~80us 结束
            err = 'ack low stuck'
        elif _wait_level(io, 0) < 0:          # ACK 高 ~80us 结束
            err = 'ack high stuck'
        else:
            # --- 40 bit:50us 低 + [26-28us=0 / 70us=1] 高 ---
            for i in range(40):
                if _wait_level(io, 1) < 0:    # 每 bit 起始低电平结束
                    err = 'data low timeout'
                    break
                hi = _wait_level(io, 0)       # 高电平宽度(us)
                if hi < 0:
                    err = 'data high timeout'
                    break
                data[i // 8] = (data[i // 8] << 1) | (1 if hi > BIT1_THRESH_US else 0)
    finally:
        io.init(Pin.OUT, value=1)             # 空闲态保持高,方便下次起始

    if err:
        return None, err

    rh_i, rh_d, t_i, t_d, chk = data
    if (rh_i + rh_d + t_i + t_d) & 0xFF != chk:
        return None, 'checksum error'
    return (rh_i + rh_d * 0.1, t_i + t_d * 0.1), None


def main():
    print('DHT11 on', DHT_PIN)
    time.sleep_ms(1000)                       # 上电稳定(DHT11 需 >1s)
    while True:
        for attempt in range(MAXRETRY):
            res, err = dht11_read(DHT_PIN)
            if res:
                rh, temp = res
                print('Temp: %.1f C   Humidity: %.1f %%' % (temp, rh))
                break
            print('read failed:', err)
            time.sleep_ms(60)
        else:
            print('DHT11 not responding after %d tries' % MAXRETRY)
        time.sleep_ms(1500)                   # DHT11 采样周期 >=1s


main()
