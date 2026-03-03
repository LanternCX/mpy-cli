# 部署与发布文档

## 本地部署到设备

1. 确认已安装 `mpremote`：

```bash
python3 -m pip install mpremote
```

2. 预览部署计划：

```bash
mpy-cli plan --port /dev/ttyACM0
```

3. 执行部署：

```bash
mpy-cli deploy --port /dev/ttyACM0
```

## 发布流程

- 推送 Tag（例如 `v0.1.0`）后自动触发 GitHub Actions。
- 工作流会执行测试并打包四个平台产物：
  - mac-arm64（tar.gz）
  - linux-arm64（tar.gz）
  - linux-x64（tar.gz）
  - windows-x64（zip）
- 自动创建 draft release 并上传构建产物。

## 发布产物内容

- Python 源码目录 `mpy_cli/`
- `README.md`
- `pyproject.toml`
- `assets/default-config.toml`
- `assets/runtime.db`
