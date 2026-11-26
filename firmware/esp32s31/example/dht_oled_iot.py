import machine
import dht
import time
import network
from umqtt.simple import MQTTClient
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
# ========== 配置信息 ===========
# WiFi 信息
WIFI_SSID = "D106-108"
WIFI_PASSWORD = "kobe2016"

# 小猫物联网平台 MQTT 配置
MQTT_CLIENT_ID = "sensor_dht"  # 自定义ID
MQTT_BROKER = "iot.kittenbot.cn"
MQTT_PORT = 1883
# 发布主题
TOPIC_TEMP = "ljl/dht/temperature"
TOPIC_HUMI = "ljl/dht/humidity"

# ==== Initialized IIC OLED ====
i2c=I2C(0,sda=Pin(48), scl=Pin(47), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

def display_TH(temp,humi):
    oled.fill(0)
    oled.text("Temperature:", 0, 0)
    oled.text("{:.1f} C".format(temp), 20, 15)
    oled.text("Humidity:", 0, 35)
    oled.text("{:.1f} %".format(humi), 20, 50)
    oled.rotate(1)
    oled.show()
    
# DHT11 引脚
d = dht.DHT11(machine.Pin(1))

# WiFi 连接函数
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("正在连接WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("WiFi连接成功！IP:", wlan.ifconfig()[0])

# MQTT 连接函数
def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    try:
        client.connect()
        print("MQTT连接小猫物联网平台成功！")
        return client
    except Exception as e:
        print("MQTT连接失败:", e)
        return None

# 主程序
def main():
    # 连接WiFi
    connect_wifi()
    # 连接MQTT
    client = connect_mqtt()
    if not client:
        print("MQTT连接失败，程序退出")
        return
    
    print("开始上传温湿度数据...")
    while True:
        try:
            # 读取DHT11数据
            d.measure()
            t = d.temperature()
            h = d.humidity()
            
            # 串口打印
            print('Temperature: {}°C'.format(t))
            print('Humidity: {}%'.format(h))
            # OLED 显示
            display_TH(t,h)
            
            # 发布到MQTT
            client.publish(TOPIC_TEMP, str(t))
            client.publish(TOPIC_HUMI, str(h))
            print("数据上传成功")
            
        except OSError as e:
            print("读取传感器失败，正在重试...")
            # 出错后重新连接MQTT
            client = connect_mqtt()
        
        # 2秒上传一次
        time.sleep(2)

# 运行主程序
if __name__ == "__main__":
    main()
