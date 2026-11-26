# SPI：Arduino D10..D13 = P301/P110/P109/P111 = 板上 spi0(RSPI0)，
# 与 Pmod1 的 1..4 脚是同一组网络（E36 默认闭合）。
# CS 用软件片选更灵活（rspi 的硬件 SSLA0 也在 D10 上）。
from machine import SPI, Pin

spi = SPI("spi0")                        # 板级 dts 已配好 4 个 psel
cs = Pin("D10", Pin.OUT, value=1)        # 软件 CS

# 读 4 字节（MOSI 悬空时通常读到 0x00 或 0xFF）
buf = bytearray(4)
cs.value(0)
spi.write_readinto(b"\xaa\x55\xaa\x55", buf)
cs.value(1)
print("SPI 回读:", buf.hex())

# 自测：把 D11(MOSI) 与 D12(MISO) 短接，应打印 5aa55aa5
out = b"\x5a\xa5\x5a\xa5"
rx = bytearray(len(out))
cs.value(0)
spi.write_readinto(out, rx)
cs.value(1)
print("发送:", out.hex(), "接收:", rx.hex(), "一致" if rx == out else "不一致（检查接线）")
