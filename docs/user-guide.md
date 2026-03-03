# 用户文档

## 项目介绍

`mpy-cli` 用于将本地项目文件部署到 MicroPython 设备，支持：

- `.mpyignore` 文件忽略机制
- 全量部署（清空设备后上传）
- 增量部署（基于 `git diff`）
- 交互式命令流程（questionary）

## 常用命令

```bash
mpy-cli init
mpy-cli plan --port /dev/ttyACM0
mpy-cli deploy --port /dev/ttyACM0
```

## 配置说明

初始化后会生成 `.mpy-cli.toml`：

```toml
serial_port = ""
ignore_file = ".mpyignore"
runtime_dir = ".mpy-cli"
source_dir = "."
mpremote_binary = "mpremote"

[sync]
mode = "incremental"
```

- 将 `sync.mode` 设为 `full` 可切换为全量模式。
- `runtime_dir` 下保存运行日志与运行时数据库。
