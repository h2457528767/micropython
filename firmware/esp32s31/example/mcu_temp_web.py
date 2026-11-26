import network, socket, esp32, time
from machine import reset

WIFI_SSID = "D106-108"
WIFI_PASS = "kobe2016"
PORT = 8080

# 连接WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)
while not wlan.isconnected():
    time.sleep(0.5)
ip = wlan.ifconfig()[0]
print(f"IP: {ip}:{PORT}")

# 网页
HTML = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
<meta http-equiv="refresh" content="1">
<meta charset="utf-8">
<h1>ESP32-S31 Temperature: %s&#176;C</h1>"""

# 启动服务器
addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print("Server running...")

while True:
    try:
        cl, _ = s.accept()
        cl.recv(1024)
        temp = esp32.mcu_temperature()
        cl.send(HTML % f"{temp:.1f}")
        cl.close()
    except:
        pass