# https://docs.micropython.org/en/v1.29.0/zephyr/quickref.html
from machine import PWM

#pwm = PWM(("pwm1", 0), freq=3921568, duty_ns=200, invert=True)    # create pwm on [PWM1, ch0] -> D5 / P409
pwm = PWM(("pwm1", 1), freq=3921568, duty_ns=200, invert=True)    # create pwm on [PWM1, ch1] -> D3 / P408
print(pwm)                                                        # print pwm

print(pwm.duty_ns())                                              # print pwm duty cycle in nanoseconds
pwm.duty_ns(255)                                                  # set new pwm duty cycle in nanoseconds

pwm.deinit()