# 上游来源与整合取舍

调研日期：2026-10-08。通过 GitHub 检索后读取以下固定提交中的原始文件。所有来源在调研时均为 MIT 许可。这里记录机制参考；本项目的中文指令、检查器与模板为针对本需求编写，未复制上游脚本或整套技能正文。

## planning-with-files

仓库：[OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files)。

固定提交：[41f60ae](https://github.com/OthmanAdi/planning-with-files/commit/41f60aeca8bae0b145ec0e9421a7abd747ae2b69)。许可：[MIT](https://github.com/OthmanAdi/planning-with-files/blob/41f60aeca8bae0b145ec0e9421a7abd747ae2b69/LICENSE)。

阅读文件：

- [skills/planning-with-files/SKILL.md](https://github.com/OthmanAdi/planning-with-files/blob/41f60aeca8bae0b145ec0e9421a7abd747ae2b69/skills/planning-with-files/SKILL.md)

采用：任务状态写入文件；行动前恢复当前计划；区分任务目录与技能安装目录。

适配：优先引用已有计划；用一个任务 ID 和一份短恢复摘要避免出现竞争计划。

## Agent Skills for Context Engineering

仓库：[muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)。

固定提交：[58b55a8](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/commit/58b55a8921758d13453b440704fb1b5b208c0b0e)。许可：[MIT](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/58b55a8921758d13453b440704fb1b5b208c0b0e/LICENSE)。

阅读文件：

- [skills/context-degradation/SKILL.md](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/58b55a8921758d13453b440704fb1b5b208c0b0e/skills/context-degradation/SKILL.md)
- [skills/context-compression/SKILL.md](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/58b55a8921758d13453b440704fb1b5b208c0b0e/skills/context-compression/SKILL.md)

采用：标注冲突规则来源；在摘要中保留有效约束、产物位置与版本；用恢复问题核对接续能力。

适配：从当前失焦现象选择处理方法；不把未经本任务测量的上下文比例或性能阈值设为事实。

## superpowers

仓库：[obra/superpowers](https://github.com/obra/superpowers)。

固定提交：[8ca22db](https://github.com/obra/superpowers/commit/8ca22dba9a94f28898bbce59f2537ff4d87c747d)。许可：[MIT](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/LICENSE)。

阅读文件：

- [skills/verification-before-completion/SKILL.md](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/verification-before-completion/SKILL.md)
- [skills/executing-plans/SKILL.md](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/executing-plans/SKILL.md)

采用：完成声明对应验证证据；工作步骤带预期结果；偏离计划的决定留下理由。

适配：保留用户当前授权，省去常规步骤的再次确认；不引入整套开发方法或强制额外代理。

## GSD

仓库：[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)。

固定提交：[bdcaab2](https://github.com/gsd-build/get-shit-done/commit/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815)。许可：[MIT](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/LICENSE)。

阅读文件：

- [get-shit-done/templates/state.md](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/get-shit-done/templates/state.md)

采用：保留当前阶段、已完成动作、下一步与暂缓事项，使任务可跨会话恢复。

适配：用短检查点连接现有工作流；不安装新的运行时、hooks 或跨项目记忆。

## 本地已有技能的边界

planning-with-files 继续管理既有计划；handoff 继续承载交接文档。focus 负责当前问题的诊断、指标、规则裁决与执行恢复，引用现有产物即可。SKILL.md 主线和 workflow.md 是本技能行为的维护来源；此文件只用于审查来源或后续升级，不必在每次聚焦时加载。

## 验证范围

结构检查、只读工具测试与人工场景审阅只能证明已检查的机制。没有声称本技能已经降低真实长程任务失败率；在实际任务上保存基线、纠偏周期和恢复探针结果后，再根据观测调整阈值。
