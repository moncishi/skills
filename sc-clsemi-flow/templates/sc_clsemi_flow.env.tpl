# sc_clsemi_flow 环境配置（项目级，随项目走）— 由 /sc-clsemi-flow init 从模板生成
# 所有环境参数只从这里取，流程零硬编码
# {{...}} 占位符只有 5 个项目特有值，由 init 收集替换；其余为环境设施默认值（同一套
# 编译/调试环境下一般不变），换服务器/换 PC/换串口直接改对应行即可
#   占位符：PROJECT_ROOT SDK_ROOT DOCKER_CONTAINER BUILD_TARGET GIT_BRANCH

# ===== 工程与编译 =====
PROJECT_ROOT={{PROJECT_ROOT}}                 # 工作区根（.zcode 运行日志等相对路径的锚点）
SDK_ROOT={{SDK_ROOT}}
DOCKER_CONTAINER={{DOCKER_CONTAINER}}
DOCKER_USER=gryphon                           # docker 执行用户（环境设施默认）
BUILD_TARGET={{BUILD_TARGET}}                 # 板型（wa7220-g / wa7230-g），换板改这里
GIT_BRANCH={{GIT_BRANCH}}                     # 主分支名（init 默认给 master）
BUILD_DOC=.zcode/build_flow.md                # 编译+制档引导文档（项目级，阶段 4 按它执行）

# ===== 编译服务器 =====
SERVERIP=172.21.53.68
SSH_USER=gryphon
SSH_PASS=123456

# ===== DUT（板子）=====
BOARD_IP=192.168.1.1
BOARD_USER=admin                              # 刷机默认账号（uid=0，等效 root）
BOARD_PASS=!QAZ2wsx                           # 刷机默认密码，每次刷完自动恢复——自动化统一用这组（跨刷机稳定）
DUT_TUNNEL_PORT=19400                         # 服务器侧反向隧道端口（DUT SSH 验证走 127.0.0.1:此端口）
TELNET_TUNNEL_PORT=19200                      # 备用（DUT telnet）
ENTERBOOT_VAR=enterboot                       # bootcmd 已固化 enterboot 检查（=1 则停 U-Boot）
                                              # 实测：刷机后 env 分区保留，enterboot=1 会残留
                                              # → 刷写完成后在 U-Boot 里 setenv enterboot 0; saveenv 再 boot

# ===== PC 通道 =====
MCP_URL=http://172.21.53.161:3456/mcp
SERVERIP_PC=192.168.1.10                      # PC 在 DUT 网段的 IP（U-Boot serverip，需与 DUT 互通）
WORK_DIR_PC=D:\ica-mcp                        # PC 交换目录（=TFTPD32 服务目录）
# 服务器密码用上方 SSH_PASS（file_pull / tunnel_control 的 password 参数从这取）

# ===== 串口 =====
SERIAL_PORT=COM20
SERIAL_BAUD=9600

# ===== U-Boot 交互 =====
UBOOT_CMDS_FILE=.zcode/uboot_flash_cmds.txt   # 刷机命令序列（项目级文件，每行一条）
UBOOT_PROMPT="re:=>"
LINUX_PROMPT="re:#\s*$"                       # Linux shell 提示符以 # 结尾（如 root@OpenWrt:~#）
BOOT_DONE_PATTERN="Please press Enter to activate this console"

# ===== 邮件 =====
MAIL_CONF=sc_script/tools/mail.conf           # send_mail.py 同目录的凭据文件（用户级，勿进 git）
MAIL_TO=75966308@qq.com,gryphon_shi@sercomm.com
