# U-Boot 刷机命令序列（项目级，每行一条，流程逐行经 serial_expect_send 执行）— 由 /sc-clsemi-flow init 从模板生成
# 固件名随 BUILD_TARGET 变化：{{BUILD_TARGET}}_nand.bin
#
# 提示符：U-Boot 提示符是 "=>"（每条命令执行完回显它）；Linux shell 提示符以 "#" 结尾
#
# 执行规则（首刷演练实测教训）：
# - 每行 send 后的 post_pattern 用 "re:=>"，但 "ping" 行 timeout 90（PHY 初始化慢）
# - tftp 行 timeout 300；完成后必须核对 "Bytes transferred = <整包字节数>"
#   （整包大小从阶段 4 产物校验取，如 wa7230-g = 55574528；首次实测曾在 124KB 处静默中断）
#   核对不一致→重跑 tftp，最多 3 次；仍不一致停下报告，绝不带病刷写
# - 刷写前数据抽查（U-Boot 无 md5sum，crc32 也未必有）：头尾各 16 字节与服务器侧整包比对：
#     md.b 0x400000 16
#     md.b 0x400000+<整包字节数>-0x10 16     （地址按大小现算；wa7230-g 即 0x38FFBF0）
#   服务器侧取对照：xxd -l 16 <整包>（头）；xxd -s -16 <整包>（尾）
# - mtd erase/write（run upgrade_all）timeout 300+（实测约 20-40 秒完成，跳过出厂坏块属正常）
# - 全部命令执行完后、boot 之前：先在 U-Boot 执行 setenv {{ENTERBOOT_VAR}} 0; saveenv
#   （enterboot=1 刷机后残留，boot 会重跑 bootcmd 又停在 U-Boot），再发 boot
# - boot 的完成标志: "Please press Enter to activate this console."

setenv ipaddr {{BOARD_IP}}
setenv serverip {{SERVERIP_PC}}
ping {{SERVERIP_PC}}
tftp 0x400000 {{BUILD_TARGET}}_nand.bin
setenv do_old 'mtd read spi-nand0 0x1400000 0x400000 0x200000;mtd erase spi-nand0 0 0x5000000;mtd write spi-nand0 0x400000 0 $filesize;'
setenv do_new 'mtd read spi-nand0 0x1400000 0x1000000 0x200000;mtd erase spi-nand0 0 0x5000000;mtd write spi-nand0 0x400000 0 $filesize;'
setenv upgrade_all 'mtd read spi-nand0 0x1400000 0x400000 0x200000;if itest.l *0x1400000 == 0x00088b1f; then echo "do old" && run do_old; else echo "do new" && run do_new; fi'
run upgrade_all
