# 编译与最终 bin 档制作（项目级引导文档）— 由 /sc-clsemi-flow init 从模板生成

由 sc-clsemi-flow 阶段 4 读取并执行。目标默认 **{{BUILD_TARGET}}**（当前 DUT）。

> **目标切换说明**：命令中的 `{{BUILD_TARGET}}` 视作 env 的 `$BUILD_TARGET`、
> `{{BUILD_TARGET}}_nand.bin` 视作 `${BUILD_TARGET}_nand.bin`、`mfg-{{BUILD_TARGET}}` 视作 `mfg-$BUILD_TARGET`。
> 换目标只改 env 的 `BUILD_TARGET`，执行时按此替换，无需改本文档。

**日志规则**：
- 第 1 步详细编译日志 → `.zcode/build_flow_openwrt.log`（首行写编译时间，追加模式）
- 第 2 步详细制档日志 → `.zcode/build_flow_firmware.log`（首行写制作时间，追加模式）
- 标准输出与标准错误**都重定向**（`>> 文件 2>&1`），方便 debug
- 阶段状态摘要（通过/失败、md5、版本时间戳）→ `.zcode/sc_clsemi_flow.log`
- debug 时用 `tail`/`grep` 查看日志；错误检查用 `grep "^ERROR"`（行首匹配，避免 V=s 回显脚本文本误报）

## 第 0 步：记录编译开始时刻（防旧残留假通过）

```bash
T0=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S'); echo "$T0"   # 记入运行日志，第 3 步要用
```

## 第 1 步：docker 内全量编译

容器 `{{DOCKER_CONTAINER}}`，主机 SDK 所在树以相同路径 bind-mount 进容器
（**容器内 SDK 路径与主机一致**）。按约定用 `-u {{DOCKER_USER}}` 执行。

```bash
LOG={{PROJECT_ROOT}}/.zcode/build_flow_openwrt.log
echo "===== 编译时间: $(date '+%Y-%m-%d %H:%M:%S') TARGET: {{BUILD_TARGET}} =====" >> "$LOG"
docker exec -u {{DOCKER_USER}} {{DOCKER_CONTAINER}} bash -c \
  "cd {{SDK_ROOT}} && ./build.sh {{BUILD_TARGET}}" \
  >> "$LOG" 2>&1
echo "exit_code=$?" >> "$LOG"
```

build.sh 内部顺序（任一段失败即终止；前置拷贝内容随 SDK 版本而异，**以实际 build.sh 为准**）：
power table / DTS / sercomm 脚本拷贝 → 写 sercomm_prj → `uboot-clsemi{clean,compile}` → `sercomm-tools{clean,compile}` → `sercomm-tools-ver{clean,compile} -j1` → `make -j6`

**失败处理**：读 `$LOG` 完整日志定位（`tail -100 "$LOG"`、`grep "^ERROR" "$LOG"`）→ 修复 → 重试，最多 3 轮；仍失败停下向用户报告（带日志摘录）。

## 第 2 步：mfg 链路（先做 boot，再做完整镜像）

均在容器内执行（路径与主机一致），mfg 目录跟目标走（`mfg-<TARGET>`）：

```bash
LOG={{PROJECT_ROOT}}/.zcode/build_flow_firmware.log
echo "===== 制作时间: $(date '+%Y-%m-%d %H:%M:%S') TARGET: {{BUILD_TARGET}} =====" >> "$LOG"
docker exec -u {{DOCKER_USER}} {{DOCKER_CONTAINER}} bash -c \
  "cd {{SDK_ROOT}}/mfg-{{BUILD_TARGET}}/bootloader_pack_tool && ./sc_gen_img.sh \
   && cd {{SDK_ROOT}}/mfg-{{BUILD_TARGET}}/sp328-programmer-cs8862a-golden-img-tool/mkbin \
   && ./create_cl_image.sh && ./create_nand.sh" \
  >> "$LOG" 2>&1
echo "exit_code=$?" >> "$LOG"
```

- `sc_gen_img.sh`：从 build_dir 取 u-boot.bin 打包 boot
- `create_cl_image.sh`：调 boot 打包 + sc_gen_goldimg.sh 生成 golden image
- `create_nand.sh`：拷 goldenimage MFST + scBind_new 绑定 → **`{{BUILD_TARGET}}_nand.bin`**（整包）

> **SoC 标注**：mfg 路径中 `sp328-programmer-cs8862a-golden-img-tool` 的目录名含 SoC 型号（cs8862a）——
> CS8862A 项目（wa7220-g / wa7230-g）直接可用；将来换 SoC 的项目需手改本节 mfg 路径。

**失败处理**：同第 1 步，查 `$LOG` 定位。

## 第 3 步：产物校验（记录到 sc_clsemi_flow.log）

```bash
PKG={{SDK_ROOT}}/mfg-{{BUILD_TARGET}}/sp328-programmer-cs8862a-golden-img-tool/mkbin/{{BUILD_TARGET}}_nand.bin
ls -l "$PKG"
md5sum "$PKG"
TS=$(find {{SDK_ROOT}}/build_dir -name "_sercomm_build_time.txt" -exec cat {} \; | sort -r | head -1)
echo "版本时间戳: $TS"
```

**通过标准**：
1. 整包存在 + md5 落盘
2. **版本时间戳 TS ≥ 第 0 步的 T0**（均按 Asia/Shanghai 比较）——防 build_dir 旧残留导致假通过；TS 早于 T0 = 读到了旧文件，定位正确的 `_sercomm_build_time.txt`（sercomm-tools-ver 的 FORCE 重编产物）或重编后复查
3. 全过 = 编译阶段通过，流程进入部署阶段（阶段 5）
