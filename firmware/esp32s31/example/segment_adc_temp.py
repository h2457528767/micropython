from machine import Pin, ADC
import esp32, time

# 74HC595 引脚
latch = Pin(36, Pin.OUT)
clock = Pin(37, Pin.OUT)
data  = Pin(38, Pin.OUT)

# 共阳数码管段码
smgduan = [
    0b11000000, # 0
    0b11111001, # 1
    0b10100100, # 2
    0b10110000, # 3
    0b10011001, # 4
    0b10010010, # 5
    0b10000010, # 6
    0b11111000, # 7
    0b10000000, # 8
    0b10010000, # 9
]

# 595 发送数据
def shift_out(byte):
    for i in range(8):
        bit = (byte >> (7 - i)) & 1
        data.value(bit)
        clock.value(1)
        clock.value(0)

# 显示函数
def show(left, right, dot=False):
    seg_l = smgduan[left % 10]
    seg_r = smgduan[right % 10]
    if dot:
        seg_r &= 0b01111111  # 共阳小数点亮

    latch.value(0)
    shift_out(seg_r)
    shift_out(seg_l)
    latch.value(1)

# 温度读取
#sensor_temp = ADC(4)
#conv = 3.3 / 65535

# 动态显示主循环
while True:
    #reading = sensor_temp.read_u16() * conv
    #temp = 27 - (reading - 0.706) / 0.001721
    temp = esp32.mcu_temperature()
    # ====================== 智能显示逻辑 ======================
    if temp >= 10:
        # 两位数 → 显示整数 如 26、31
        temp_round = round(temp, 0)
        left = int(temp_round // 10)
        right = int(temp_round % 10)
        show(left, right, dot=False)
    else:
        # 个位数 → 显示小数点 如 7.9
        temp_round = round(temp * 10) / 10
        left = int(temp_round)
        right = int((temp_round * 10) % 10)
        show(left, right, dot=True)
    
    print("Temp: {:.1f} °C".format(temp))
    time.sleep(0.5)