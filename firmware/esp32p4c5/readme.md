
### P4 固件上传

```bash
esptool --chip esp32p4 -p COM30 -b 1500000 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 16MB --flash-freq 40m 0x2000 bootloader.bin 0x8000 partition-table.bin 0x10000 micropython.bin
```



### C5 固件上传



```bash
esptool --chip esp32c5 -p COM31 -b 1500000 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 4MB 0x2000 bootloader.bin 0xc000 partition-table.bin 0xf000 ota_data_initial.bin 0x20000 network_adapter.bin
```

