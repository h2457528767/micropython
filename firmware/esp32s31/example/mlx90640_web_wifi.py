from machine import I2C
import network
import socket
import time
from mlx90640 import MLX90640, RefreshRate

# ========== WiFi配置 ==========
WIFI_SSID = "D106-108"
WIFI_PASS = "kobe2016"

temperature_frame = [0.0] * 768
last_frame_ts = 0
FRAME_INTERVAL = 1/4   # 4Hz

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>MLX90640 网页热成像 4Hz</title>
<style>
body{background:#111;color:#fff;font-family:Arial;}
#thermalCanvas{border:2px solid #444;}
.info{margin:10px 0;font-size:18px;}
.colorbar{width:30px;height:400px;background:linear-gradient(#ff0000,#ffff00,#00ffff,#0000ff);display:inline-block;vertical-align:top;margin-left:15px;}
.container{display:flex;align-items:center;}
</style>
</head>
<body>
<div class="info">MLX90640 32×24 红外热成像 | 4Hz</div>
<div class="container">
<canvas id="thermalCanvas" width="640" height="480"></canvas>
<div class="colorbar"></div>
</div>
<div class="info" id="tempInfo">等待数据...</div>
<script>
const canvas = document.getElementById('thermalCanvas');
const ctx = canvas.getContext('2d');
const w = 32, h = 24;
const pw = canvas.width / w;
const ph = canvas.height / h;

function temp2rgb(t, tmin, tmax){
    let v = (t - tmin)/(tmax - tmin);
    v = Math.max(0, Math.min(1, v));
    let r=0,g=0,b=0;
    if(v<0.25){b=1;g=v*4;}
    else if(v<0.5){g=1;b=1-(v-0.25)*4;}
    else if(v<0.75){r=(v-0.5)*4;g=1;b=0;}
    else{r=1;g=1-(v-0.75)*4;b=0;}
    return [Math.round(r*255),Math.round(g*255),Math.round(b*255)];
}

async function updateFrame(){
    try{
        const res = await fetch("/data");
        const txt = await res.text();
        const arr = txt.split(',').map(Number);
        let tmin = arr[768], tmax=arr[769], tavg=arr[770];
        document.getElementById("tempInfo").innerText =
            `最低:${tmin.toFixed(2)}℃ | 最高:${tmax.toFixed(2)}℃ | 平均:${tavg.toFixed(2)}℃`;
        ctx.clearRect(0,0,canvas.width,canvas.height);
        for(let y=0;y<h;y++){
            for(let x=0;x<w;x++){
                let t = arr[y*32+x];
                let [r,g,b] = temp2rgb(t, tmin, tmax);
                ctx.fillStyle=`rgb(${r},${g},${b})`;
                ctx.fillRect(x*pw,y*ph,pw,ph);
            }
        }
    }catch(e){
        console.log("获取数据失败");
    }
}
setInterval(updateFrame,250);
</script>
</body>
</html>
"""

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("连接WiFi:", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.3)
            print(".",end="")
    ip = wlan.ifconfig()[0]
    print("\nWiFi已连接, ESP32S3 IP地址:", ip)
    return wlan

# Web服务初始化
def init_web():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Web服务启动，浏览器打开上面IP即可访问热成像页面")
    return s

# ---------------- 传感器初始化 ----------------
time.sleep(3)
print("FreakStudio:Testing the MLX90640 fractional infrared temperature sensor")
i2c = I2C(0, scl=3, sda=2, freq=100000)
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
mlxaddr = next((d for d in devices_list if 0x31 <= d <= 0x35), None)

try:
    thermal_camera = MLX90640(i2c, mlxaddr)
    print("MLX90640 sensor initialized successfully")
except ValueError as init_error:
    print(f"Sensor initialization failed: {init_error}")
    raise SystemExit(1)

print(f"Device serial number: {thermal_camera.serial_number}")
# 设置4Hz刷新率
try:
    thermal_camera.refresh_rate = RefreshRate.REFRESH_4_HZ
    print(f"Refresh rate set to {thermal_camera.refresh_rate} Hz")
except ValueError as rate_error:
    print(f"Failed to set refresh rate: {rate_error}")
    raise SystemExit(1)
thermal_camera.emissivity = 0.92

wlan = connect_wifi()
sock = init_web()

# 主循环：轮询采集 + 处理web请求，单线程无I2C冲突
while True:
    now = time.ticks_ms()
    # 定时采集，4Hz
    if time.ticks_diff(now, last_frame_ts) >= FRAME_INTERVAL*1000:
        try:
            thermal_camera.get_frame(temperature_frame)
        except (RuntimeError, ValueError) as e:
            # 捕获math domain error，丢帧重试，不崩溃
            print(f"Frame read error, skip frame: {e}")
            continue
        last_frame_ts = now
        min_temp = min(temperature_frame)
        max_temp = max(temperature_frame)
        avg_temp = sum(temperature_frame) / len(temperature_frame)

    # 非阻塞accept，超时很短
    sock.settimeout(0.01)
    try:
        conn, addr = sock.accept()
        request = conn.recv(1024).decode()
        if "/data" in request:
            send_data = ",".join([f"{v:.2f}" for v in temperature_frame])
            send_data += f",{min_temp:.2f},{max_temp:.2f},{avg_temp:.2f}"
            response = "HTTP/1.1 200 OK\r\nContent-Type:text/plain\r\n\r\n" + send_data
            conn.send(response)
        else:
            response = "HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n" + HTML
            conn.send(response)
        conn.close()
    except OSError:
        # accept超时，继续循环读取传感器
        pass
