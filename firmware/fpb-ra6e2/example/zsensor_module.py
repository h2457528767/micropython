import zsensor

# 列出模块内容
print(dir(zsensor))


s = zsensor.Sensor("dietemp")
print(dir(s))

# 先 measure 再读
s.measure()
print(s.get_float(zsensor.DIE_TEMP))   # 若 DIE_TEMP 常量存在



