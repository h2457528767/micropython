from machine import Pin
import machine, dht, time

# DHT11 引脚
d = dht.DHT11(machine.Pin(1))

# 主程序
def main():
    print("开始读取温湿度数据...")
    while True:
        try:
            # 读取DHT11数据
            d.measure()
            t = d.temperature()
            h = d.humidity()
            
            # 串口打印
            print('Temperature: {}°C'.format(t))
            print('Humidity: {}%'.format(h))
            print("数据读取成功")
            
        except OSError as e:
            print("读取传感器失败，正在重试...")
        
        time.sleep(2)

# 运行主程序
if __name__ == "__main__":
    main()
