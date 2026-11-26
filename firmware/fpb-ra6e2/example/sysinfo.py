# 固件与系统信息：版本、堆、模块、machine 里可用的类。
import sys, gc

try:
    import os
except ImportError:
    os = None

_np = 0
_nf = []


def chk(cond, msg):
    global _np
    if cond:
        _np += 1
        print("  [PASS] " + msg)
    else:
        _nf.append(msg)
        print("  [FAIL] " + msg)
    return bool(cond)


print("===== 固件与系统信息 =====")
print("  sys.version            : " + sys.version.replace("\n", " / "))
print("  implementation         : %s %s" % (sys.implementation.name, sys.implementation.version))

gc.collect()
free, alloc = gc.mem_free(), gc.mem_alloc()
print("  MicroPython 堆          : free %d B / alloc %d B / 合计 %d B" % (free, alloc, free + alloc))
chk(free > 4096, "堆可用 > 4 KB（当前 %d B）" % free)

mods = sorted(sys.modules)
print("  已注册模块              : " + ", ".join(mods))

import machine
have = dir(machine)
print("  machine 内容            : " + ", ".join(have))

for cls in ("Pin", "ADC", "PWM", "SPI", "I2C", "SoftI2C", "UART", "Timer", "WDT"):
    chk(cls in have, "machine.%s 存在" % cls)
# 端口没有 machine_dac.c：DAC 缺席是预期行为
#chk("DAC" not in have, "machine.DAC 缺席（端口无 machine_dac.c，属预期）")

# 已注册的 Zephyr 外设实例名（machine 用字符串/元组找设备）
for name, ctor in (("spi0", lambda: machine.SPI("spi0")),
                   ("adc0", lambda: machine.ADC(("adc0", 0))),
                   ("pwm1", lambda: machine.PWM(("pwm1", 0)))):
    try:
        o = ctor()
        chk(True, "外设 %s 可用 -> %r" % (name, o))
        try:
            o.deinit()
        except Exception:
            pass
    except Exception as e:
        chk(False, "外设 %s 打不开: %r" % (name, e))


print("\n----- 通过 %d，失败 %d -----" % (_np, len(_nf)))
for m in _nf:
    print("  失败: " + m)
