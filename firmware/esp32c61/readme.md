
--flash_mode dio --flash_freq 80m --flash_size 4MB
0x0 bootloader/bootloader.bin
0x10000 micropython.bin
0x8000 partition_table/partition-table.bin

## 烧录方式

终端执行指令

```bash
esptool --chip esp32c61 -b 1500000 --before default-reset --after hard-reset write-flash 0x0 bootloader.bin 0x8000 partition-table.bin 0x10000 micropython.bin
```
