# 打印本固件里 Arduino 引脚的“名字 -> 真实端口”对照，并自检三种写法是否等价。
from machine import Pin

TABLE = [
    # 名字,  (ioport 设备名, 端口内序号), 丝印功能
    ("A0",  ("ioport0", 0),  "AN000"),
    ("A1",  ("ioport0", 1),  "AN001"),
    ("A2",  ("ioport0", 2),  "AN002"),
    ("A3",  ("ioport0", 4),  "AN004"),
    ("A4",  ("ioport0", 3),  "AN007"),
    ("A5",  ("ioport0", 13), "AN011"),
    ("D0",  ("ioport4", 10), "RXD0 / REPL"),
    ("D1",  ("ioport4", 11), "TXD0 / REPL"),
    ("D2",  ("ioport1", 5),  "IRQ0"),
    ("D3",  ("ioport4", 8),  "GTIOC1B / PWM"),
    ("D4",  ("ioport5", 0),  "GPIO"),
    ("D5",  ("ioport4", 9),  "GTIOC1A / PWM"),
    ("D6",  ("ioport1", 13), "GTIOC2A"),
    ("D7",  ("ioport0", 8),  "GPIO"),
    ("D8",  ("ioport0", 6),  "GPIO"),
    ("D9",  ("ioport4", 3),  "GTIOC3A"),
    ("D10", ("ioport3", 1),  "SSLA0 / SPI SS"),
    ("D11", ("ioport1", 9),  "MOSIA"),
    ("D12", ("ioport1", 10), "MISOA"),
    ("D13", ("ioport1", 11), "RSPCKA"),
    ("SDA", ("ioport1", 1),  "SDA0（SoftI2C，需先拉高 P401）"),
    ("SCL", ("ioport1", 0),  "SCL0（SoftI2C，需先拉高 P400）"),
    ("P400", ("ioport4", 0), "SCL0 上拉使能：做 I2C 前设输出高"),
    ("P401", ("ioport4", 1), "SDA0 上拉使能：做 I2C 前设输出高"),
    ("LED1", ("ioport2", 7), "板载 LED1"),
    ("LED2", ("ioport2", 6), "板载 LED2"),
    ("SW1", ("ioport3", 4),  "板载按键"),
]

for name, tup, note in TABLE:
    p_named = Pin(name)
    p_tuple = Pin(tup)
    same = str(p_named) == str(p_tuple)
    port, pin = tup
    print("%-4s = P%s%02d  %-28s %s" % (name, port[-1], pin, note, "OK" if same else "不一致!"))
