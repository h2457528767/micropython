from machine import Pin, ADC, UART
import time

# ---------------------- 74HC595 数码管引脚 ----------------------
latch = Pin(36, Pin.OUT)
clock = Pin(37, Pin.OUT)
data  = Pin(38, Pin.OUT)

# Initialize UART 
uart = UART(1, baudrate=115200, tx=Pin(2), rx=Pin(3))

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

# ---------------------- ADC 心率传感器配置 ----------------------
adc_pin = Pin(45)        # 心率传感器OUT引脚
adc = ADC(adc_pin)
adc.atten(ADC.ATTN_11DB) # 电压范围 0~3.3V
conv_factor = 3.3 / 65535.0

# 595移位输出
def shift_out(byte):
    for i in range(8):
        bit = (byte >> (7 - i)) & 1
        data.value(bit)
        clock.value(1)
        clock.value(0)

# 双位数码管显示函数
# left:整数位，right:小数位，dot=True点亮小数点
def show(left, right, dot=False):
    seg_l = smgduan[left % 10]
    seg_r = smgduan[right % 10]
    if dot:
        seg_l &= 0b01111111  # 整数位点亮小数点，形如 1.5
    latch.value(0)
    shift_out(seg_r)
    shift_out(seg_l)
    latch.value(1)

# ---------------------- 主循环 ----------------------
while True:
    adc_val = adc.read_u16()
    voltage = adc_val * conv_factor  # 转换为电压 0~3.3V

    # 保留一位小数
    v_1dec = round(voltage * 10) / 10
    int_part = int(v_1dec)
    dec_part = int((v_1dec * 10) % 10)

    # 数码管显示 X.X
    show(int_part, dec_part, dot=True)

    # 串口打印
    uart.write(f"{adc_val}\r\n")
    print(f"Heart ADC raw:{adc_val}, Voltage:{voltage:.1f} V")
    
    time.sleep(0.2)
