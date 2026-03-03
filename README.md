# mpy-cli

`mpy-cli` 是一个面向 MicroPython 项目的交互式命令行部署工具，核心目标是替代手工逐文件烧录流程，支持全量重刷和基于 `git diff` 的增量部署。

## 快速开始

1. 安装依赖：

```bash
python3 -m pip install -e .
```

2. 初始化项目配置：

```bash
mpy-cli init
```

3. 预览部署计划：

```bash
mpy-cli plan --port /dev/ttyACM0
```

4. 执行部署：

```bash
mpy-cli deploy --port /dev/ttyACM0
```

## 文档导航

- 用户文档：`docs/user-guide.md`
- 开发文档：`docs/developer-guide.md`
- 部署与发布文档：`docs/deployment.md`
