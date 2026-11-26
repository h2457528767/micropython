# FPB-RA6E2 MicroPython 固件参数

## 硬件平台

- 开发板：FPB-RA6E2
- MCU：R7FA6E2BB3CFM，Cortex-M4F @ 100 MHz，FPU
- Code Flash：256 KB（0x00000000）
- Data Flash：4 KB（0x40100000）
- SRAM：128 KB 物理总量，固件使用主 SRAM 40 KB（0x20000000）+ 高段 SRAM1 32 KB（0x20014800）

## 固件资源

- FLASH：210,272 B / 256 KB（80.2%）
- 主 RAM：38,816 B / 40 KB（94.8%）
- SRAM1：28 KB / 32 KB（87.5%）
- MicroPython GC 堆（拆分为两段）：12 KB 主堆 + 28 KB SRAM1 堆 ≈ 40 KB 可用 Python 堆

## 软件栈

- Zephyr RTOS v4.5.0 + MicroPython（Zephyr port，commit 3d811b9，2026-11-14）
- MicroPython 特性级别：BASIC_FEATURES（含 core 语法、float、GC、os/sys 等基础模块；不含 network/socket）

## 外设功能

- UART0 控制台/REPL：115200-8-N-1（zephyr,console + shell-uart）
- GPIO：全部已使能 IoPort 端口，`machine.Pin`
- ADC：adc 通道，12-bit，内部参考，`machine.ADC`
- PWM：已启用，`machine.PWM`
- Watchdog：驱动已编译
- CRC 硬件外设已在 DTS 声明



## GPIO 引脚资源定义

| Arduino         | MCU                           | 备注                                                        |
| --------------- | ----------------------------- | ----------------------------------------------------------- |
| D0 / D1         | P410 / P411                   |  REPL 串口（SCI0 RXD0/TXD0）|
| D2              | P105                          |                                                             |
| D3              | P408                          | `PWM(("pwm1",1))` GTIOC1B                                   |
| D4              | P500                          |                                                             |
| D5              | P409                          | `PWM(("pwm1",0))` GTIOC1A                                   |
| D6 / D7         | P113 / P008                   |                                                             |
| D8 / D9         | P006 / P403                   |                                                             |
| D10             | P301                          | `spi0` 硬件从选 SSLA0                  |
| D11 / D12 / D13 | P109 / P110 / P111            | D11=MOSIA=TXD9，D12=MISOA=RXD9，D13=RSPCKA                  |
| SDA / SCL       | P101 / P100                   | I2C 需 `Pin("P401"/"P400", OUT).value(1)` 使能上拉 |
| A0…A5           | P000,P001,P002,P004,P003,P013 | AN000,001,002,004,007,011                                   |
| 3V3 / GND       | —                             | 供电参考；`IOREF` 是 3V3                                  |

