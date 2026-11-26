# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午11:14
# @Author  : 缪贵成
# @File    : main.py
# @Description :mlx90640点阵红外温度传感器模块驱动测试文件
# 详见 https://upypi.net/en/pkgs/mlx_90640_driver

from machine import I2C
import time
from mlx90640 import MLX90640, RefreshRate

# 温度数据缓冲区
temperature_frame = [0.0] * 768

time.sleep(3)
print("FreakStudio:Testing the MLX90640 fractional infrared temperature sensor")

# 初始化 I2C
i2c = I2C(0, scl=3, sda=2, freq=100000)

# 扫描 I2C 设备
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
mlxaddr = next((d for d in devices_list if 0x31 <= d <= 0x35), None)

# 初始化传感器
try:
    thermal_camera = MLX90640(i2c, mlxaddr)
    print("MLX90640 sensor initialized successfully")
except ValueError as init_error:
    print(f"Sensor initialization failed: {init_error}")
    raise SystemExit(1)

print(f"Device serial number: {thermal_camera.serial_number}")

# 设置刷新率
try:
    thermal_camera.refresh_rate = RefreshRate.REFRESH_2_HZ
    print(f"Refresh rate set to {thermal_camera.refresh_rate} Hz")
except ValueError as rate_error:
    print(f"Failed to set refresh rate: {rate_error}")
    raise SystemExit(1)

thermal_camera.emissivity = 0.92

# 主循环
try:
    while True:
        try:
            thermal_camera.get_frame(temperature_frame)
        except RuntimeError as read_error:
            print(f"Frame acquisition failed: {read_error}")
            time.sleep(0.5)
            continue

        # 统计温度
        min_temp = min(temperature_frame)
        max_temp = max(temperature_frame)
        avg_temp = sum(temperature_frame) / len(temperature_frame)

        print("\n--- Temperature Statistics ---")
        print(f"Min: {min_temp:.2f} °C | Max: {max_temp:.2f} °C | Avg: {avg_temp:.2f} °C")

        # 打印左上角 4×4 样本像素
        print("--- Sample Pixels (Top-Left 4x4) ---")
        for row in range(4):
            row_data = [f"{temperature_frame[row*32 + col]:5.1f}" for col in range(4)]
            print(" | ".join(row_data))

        # 等待下一次测量
        time.sleep(1.0 / (thermal_camera.refresh_rate + 1))

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    print("Testing process completed")