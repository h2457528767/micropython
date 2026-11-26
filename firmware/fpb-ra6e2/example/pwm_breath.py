# PWM 呼吸灯：只用 Arduino D3 / D5。
# 板上 Zephyr 已使能 pwm1 = GPT1：GTIOC1A=P409(D5)=通道0，GTIOC1B=P408(D3)=通道1。
# machine.PWM 必须给 ("pwm1", 通道) 元组。
from machine import PWM
from time import sleep_ms

pwm_d5 = PWM(("pwm1", 0), freq=1000)     # D5 / P409
pwm_d3 = PWM(("pwm1", 1), freq=1000, duty_u16=0)   # D3 / P408

duty = 0
step = 512
while True:
    pwm_d5.duty_u16(duty)
    pwm_d3.duty_u16(65535 - duty)
    print("duty=%5d" % duty)
    duty += step
    if duty <= 0 or duty >= 65535:
        step = -step
        sleep_ms(200)
    else:
        sleep_ms(20)
