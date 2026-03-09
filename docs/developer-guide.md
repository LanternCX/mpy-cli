# 开发文档

## 架构说明

- `mpy_cli/cli.py`：命令入口与交互流程。
- `mpy_cli/config.py`：配置读写与校验。
- `mpy_cli/ignore.py`：`.mpyignore` 规则匹配。
- `mpy_cli/gitdiff.py`：Git 变更解析。
- `mpy_cli/planner.py`：部署计划生成。
- `mpy_cli/backend/mpremote.py`：设备命令适配。
- `mpy_cli/executor.py`：计划执行。
- `mpy_cli/logging.py`：控制台 + 文件切片日志。

## 代码风格

- 公共函数和类使用 Doxygen 风格注释（`@brief`、`@param`、`@return`）。
- 中文项目注释统一使用中文。
- 采用高内聚低耦合设计，规划层与执行层分离。
- 静态可持久化文件统一写入项目运行目录 `.mpy-cli/`。

## Git 工作流

- 使用 Git Flow：`main`（稳定）+ `dev`（开发）。
- 默认直接在当前开发分支工作；未获维护者明确要求时，不创建额外 worktree 或功能分支。
- 提交信息使用 Angular Commit 规范。
- 每次 commit 前必须先与维护者确认。
- 未获维护者确认时，不允许为了保存进度而自动 commit。
- 如果你使用 Agent 开发每次 commit 必须携带 Agent 信息，例如：

```text
Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>
```

## Agent 规范

建议使用 [我的 Superpowers Fork](https://github.com/LanternCX/superpowers) 开发

需要遵守 TDD 工作流

- 项目技能目录：`.opencode/skills`
- 默认遵循项目技能，不使用 superpowers 默认 worktree 工作流
- 当前技能：
  - `git-workflow`
  - `code-standard`
  - `doc-maintainer`
