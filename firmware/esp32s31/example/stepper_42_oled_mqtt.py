from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import ujson
import network
from umqtt.simple import MQTTClient
import _thread
import ntptime

# =============== 用户配置 =================
WIFI_SSID = "D106-108"
WIFI_PASSWORD = "kobe2016"

MQTT_BROKER = "iot.kittenbot.cn"
MQTT_PORT = 1883
MQTT_TOPIC = "ljl/stepmotor"
CLIENT_ID = "esp32_stepmotor_01"

# =============== 引脚定义 ===================
dir_pin = Pin(36, Pin.OUT)
step_pin = Pin(37, Pin.OUT)
en_pin = Pin(38, Pin.OUT)

i2c = I2C(0, scl=Pin(47), sda=Pin(48))
oled = SSD1306_I2C(128, 64, i2c)
oled.rotate(1)  # 屏幕方向

# ================= 全局变量 ===================
current_angle = 0
speed_us = 1200
direct_text = "STOP"
running_flag = True
mqtt_client = None

# ====================== 电机参数 ======================
step_angle = 1.8          # 步距角
step_cycle = 360 / 1.8    # 200 步/圈
microMode = 8              # 1/8 细分
steps = step_cycle * microMode  # 1600 脉冲/圈
STEPS_PER_DEGREE = steps / 360  # 4.444 脉冲/度

# ================ WiFi 连接 ====================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("连接WiFi中...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep_ms(500)
    print("WiFi已连接:", wlan.ifconfig())

# =============== NTP 时间同步 =================
def sync_time():
    try:
        ntptime.host = "ntp.aliyun.com"
        ntptime.settime()
        print("NTP时间已同步（UTC）")
    except Exception as e:
        print("NTP同步失败:", e)

# ================ OLED 后台刷新线程 ===================
def screen_task():
    while running_flag:
        try:
            # UTC+8 时区转换
            now = time.localtime(time.time() + 8 * 3600)
            date_str = "{:04d}-{:02d}-{:02d}".format(now[0], now[1], now[2])
            time_str = "{:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5])

            oled.fill(0)
            oled.text(date_str, 2, 0)
            oled.text(time_str, 2, 12)
            oled.text("Dir: " + direct_text, 2, 26)
            oled.text("V: " + str(speed_us) + "us", 2, 38)
            oled.text("Angle: " + str(current_angle) + "deg", 2, 50)
            oled.show()
        except Exception as e:
            print("OLED刷新错误:", e)
        time.sleep_ms(70)

# ================ 电机控制 ======================
def run_angle(degree, speed_us):
    global direct_text, current_angle

    pulses = int(abs(degree) * STEPS_PER_DEGREE)
    current_angle = degree

    en_pin.value(0)  # 使能驱动器

    if degree > 0:
        dir_pin.value(1)
        direct_text = "CW"
    else:
        dir_pin.value(0)
        direct_text = "CCW"

    delay_us = int(speed_us)
    if delay_us < 10:
        delay_us = 10  # 下限保护，防止过快丢步

    for _ in range(pulses):
        step_pin.value(1)
        time.sleep_us(delay_us)
        step_pin.value(0)
        time.sleep_us(delay_us)

    direct_text = "STOP"
    en_pin.value(1)  # 释放扭矩
    print("Rotate %.1f degree, %d steps" % (degree, pulses))

# ====================== MQTT 回调 ======================
def on_message(topic, msg):
    global speed_us
    try:
        data = ujson.loads(msg.decode())
        # 关键：没有 angle 字段，直接忽略
        # 由于订阅和接收主题相同，防止接收到 {"result":"OK"} 后循环发送指令
        if "angle" not in data:
            return
        angle = data.get("angle", 0)
        speed_us = data.get("speed", 1200)
        print("收到指令: angle=%s, speed=%sus" % (angle, speed_us))

        run_angle(angle, speed_us)

        # 旋转完成回复 OK
        mqtt_client.publish(MQTT_TOPIC, '{"result":"OK"}')
    except Exception as e:
        print("解析错误:", e)

# =============== 主程序 ===================
def main():
    global mqtt_client, running_flag

    connect_wifi()
    sync_time()

    # 启动 OLED 后台刷新线程
    _thread.start_new_thread(screen_task, ())

    # MQTT 客户端连接
    mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.set_callback(on_message)
    mqtt_client.connect()
    mqtt_client.subscribe(MQTT_TOPIC)
    print("MQTT已连接，订阅主题:", MQTT_TOPIC)

    try:
        while True:
            mqtt_client.wait_msg()
    except KeyboardInterrupt:
        running_flag = False
        time.sleep(0.2)
        oled.fill(0)
        oled.show()
        en_pin.value(1)
        mqtt_client.disconnect()
        print("已退出")

if __name__ == "__main__":
    main()
