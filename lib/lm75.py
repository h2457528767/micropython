from machine import I2C

class LM75:
    """
    LM75/LM75B 温度传感器 MicroPython 驱动
    默认I2C地址：0x48，支持 0x48~0x4F 全地址适配
    分辨率：0.125℃
    温度范围：-55℃ ~ +125℃
    """
    def __init__(self, i2c: I2C, addr: int = 0x48):
        self.i2c = i2c
        self.addr = addr  # LM75 I2C设备地址

    def get_temp(self) -> float:
        """读取实时温度（修复原负数计算BUG）"""
        # 读取温度寄存器 0x00，2字节数据
        raw_data = self.i2c.readfrom_mem(self.addr, 0x00, 2)
        # 拼接原始16位数据
        raw = (raw_data[0] << 8) | raw_data[1]
        
        # LM75 数据格式：高11位有效，右移5位为温度基数
        temp_raw = raw >> 5
        
        # 判断正负温度（11位数据，最大值1023）
        if temp_raw < 0x400:
            # 正温度 0~125℃
            temp = temp_raw * 0.125
        else:
            # 负温度 -55~0℃
            temp = (temp_raw - 2048) * 0.125
        
        return round(temp, 3)

    def set_os(self, temp_high: float, temp_low: float = None):
        """
        设置过热阈值OS（关断温度）和滞回温度
        :param temp_high: 过热关断阈值温度
        :param temp_low:  滞回恢复温度，不传则默认等于temp_high
        """
        # 不传低阈值则默认高低阈值一致
        if temp_low is None:
            temp_low = temp_high

        # 温度转寄存器数值（LM75 温度精度 0.5℃，寄存器放大2倍）
        def temp2reg(temp: float) -> int:
            reg = int(temp * 2)
            # 11位寄存器数据限位
            return reg & 0x7FF

        # 转换阈值
        reg_high = temp2reg(temp_high)
        reg_low = temp2reg(temp_low)

        # 修复原代码字节序BUG：大端字节写入（LM75标准协议）
        # 0x03：OS过热阈值寄存器
        self.i2c.writeto_mem(self.addr, 0x03, reg_high.to_bytes(2, 'big'))
        # 0x02：滞回阈值寄存器
        self.i2c.writeto_mem(self.addr, 0x02, reg_low.to_bytes(2, 'big'))

        print(f"阈值设置完成 | 过热阈值：{temp_high}℃ | 滞回阈值：{temp_low}℃")

    def get_os_threshold(self) -> tuple[float, float]:
        """读取当前设置的 过热阈值、滞回阈值"""
        # 读取滞回阈值 0x02
        low_raw = self.i2c.readfrom_mem(self.addr, 0x02, 2)
        low_reg = (low_raw[0] << 8) | low_raw[1]
        temp_low = (low_reg & 0x7FF) / 2

        # 读取过热阈值 0x03
        high_raw = self.i2c.readfrom_mem(self.addr, 0x03, 2)
        high_reg = (high_raw[0] << 8) | high_raw[1]
        temp_high = (high_reg & 0x7FF) / 2

        return round(temp_high, 2), round(temp_low, 2)
