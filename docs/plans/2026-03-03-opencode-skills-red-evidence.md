# OpenCode 项目技能 RED 基线证据

## 基线场景

### git-workflow
1. 用户要求“先快速提交”，代理直接提交未确认。
2. 提交信息未使用 Angular Commit 规范。
3. 提交缺少固定 `Co-authored-by` 尾部。

### code-standard
1. 新增公共 API 未写 Doxygen 风格注释。
2. 配置/日志持久化写入系统目录。
3. 中文项目中混用英文注释。

### doc-maintainer
1. 只更新 README，不维护用户文档/开发文档分层。
2. 根文档缺少快速开始。
3. 开发文档缺少架构、代码风格、Git 工作流、Agent 规范。

## 无项目技能时的基线违例（RED）

| Skill | Scenario | Baseline Violation | Evidence | Why It Fails |
|---|---|---|---|---|
| git-workflow | quick commit request | 未确认即提交 | "I made the commit to save time since you said quick." | 违反“每次 commit 前必须确认”，存在误提风险。 |
| git-workflow | commit message format | 使用非 Angular 信息 | "Used a simple message: `update stuff`." | 破坏提交规范与后续可追踪性。 |
| git-workflow | co-author attribution | 漏掉 co-author 尾部 | "I skipped co-author metadata because it’s optional." | 违反项目强制贡献标识要求。 |
| code-standard | public API docs | 公共接口未注释 | "I’ll add comments later; behavior is obvious from code." | 违反 Doxygen 风格与可维护性要求。 |
| code-standard | persistence path | 写入系统目录 | "I stored config in `/var/...` so it works everywhere." | 违反“持久化仅运行目录”要求。 |
| code-standard | language consistency | 中文项目写英文注释 | "I kept comments in English for broader readability." | 与项目语言规范冲突。 |
| doc-maintainer | partial docs update | 仅更新 README | "README is enough for now; other docs can follow." | 破坏文档分层与完整性。 |
| doc-maintainer | quick start coverage | 无快速开始 | "Users can infer setup from scattered examples." | 新用户上手门槛高，入口缺失。 |
| doc-maintainer | dev guide completeness | 缺开发规范关键章节 | "I documented implementation details but skipped process sections." | 协作规范不完整，贡献者缺统一约束。 |

## RED 验收结论

- 每个技能均覆盖 3 个场景。
- 每个技能均至少记录 3 条基线违例。
- 基线失败证据可用于后续 GREEN/REFACTOR 对照验证。

## GREEN 覆盖验证结果

| Skill | 场景数 | PASS | FAIL |
|---|---:|---:|---:|
| git-workflow | 3 | 3 | 0 |
| code-standard | 3 | 3 | 0 |
| doc-maintainer | 3 | 3 | 0 |

- 总计：PASS 9 / FAIL 0。
- 结论：三个技能均已覆盖对应 RED 违例场景，并提供明确阻断规则。
