# focus

说“聚焦”，把当前长程任务恢复成 **可验证目标、明确指标、单一主工作流和可接续检查点**。

本技能处理任务跑偏、AGENTS.md 与 skills 冲突、多份 workflow 竞争、重复检索或重试，以及上下文压缩后忘记进展等问题。执行者先判断当前问题，再选能验证该问题的方法，并继续用户已授权的工作。

## 使用

安装后可以直接说：

```text
聚焦
聚焦当前任务：先整理规则冲突，给出指标与下一步
$focus
```

技能要求输出一张针对当前任务的聚焦卡：

| 内容 | 应给出的事实 |
| --- | --- |
| 当前问题 | 原始目标、当前瓶颈和失焦原因的证据 |
| 验收指标 | 基线、目标、当前值、验证方法与证据 |
| 工作流 | 每步对应的指标、产物和预期检查结果 |
| 下一步 | 一个可以直接执行的验证动作 |
| 恢复点 | 有效约束、已验证产物与版本、未完成项 |

默认方法：**恢复现场 → 诊断失焦 → 定义指标 → 执行并测量 → 验收与保存恢复点**。根据任务裁剪；一般执行选择自主判断，必要信息缺失才提问。

## 指标

结果指标来自当前任务，例如同一输入的故障复现、固定验证集的实验收益，或文稿的事实与版式清单。过程指标用于发现工作流失焦：

| 指标 | 默认约定 |
| --- | --- |
| 已记录验证覆盖 | 验收时所有必要指标都有版本对应的证据 |
| 动作对齐率 | 100%，每步关联至少一个结果指标 |
| 当前主步骤 | 默认 1 个 doing；已有授权的协作保留在原计划 |
| 待裁决规则冲突 | 当前动作相关冲突为 0 |
| 无证据通过声明 | 0 |
| 无新证据连续周期 | 未完成任务达到 2 次就重新聚焦并换方法 |

“两次”是可调整的初始阈值。覆盖率统计记录齐全程度，不等于整体任务完成百分比。真实内容、输入和产物版本仍要核对；不得编造“聚焦分数”或实测改进幅度。

## 安装与源码同步

仓库中的 `skills/focus` 是维护来源，安装副本默认位于 `~/.codex/skills/focus`；设置 CODEX_HOME 时使用该目录。

在仓库根目录的 PowerShell 中运行：

```powershell
.\scripts\install.ps1
.\scripts\install.ps1 -Mode Check
```

修改源码后先核对差异，再执行：

```powershell
.\scripts\install.ps1 -Force
.\scripts\install.ps1 -Mode Check
git add -- README.md AGENTS.md .gitignore .gitattributes LICENSE skills/focus scripts/install.ps1 tests
git commit -m "Update focus workflow"
git push origin main
```

安装脚本只复制技能文件，Check 用 SHA-256 对比源码与安装文件。GitHub 同步使用当前用户已有认证。任务检查点、项目资料和聊天记录保存在原任务目录，不能提交到这个技能仓库。

技能通过描述和本地文件提供执行约定。本版本未接入宿主生命周期 hooks；跨会话恢复依赖代理重新读取检查点，可再次说“聚焦”显式恢复。

## 只读检查与验证

无既有恢复位置时，任务状态放在 `.focus/<task-id>/focus.json`。已有计划通过 plan_ref 引用，避免维护第二份完整计划。状态字段、指标口径与恢复探针见 [工作流约定](skills/focus/references/workflow.md)。

```text
python <skill-dir>/scripts/focus_check.py <task-dir>/focus.json
python <skill-dir>/scripts/focus_check.py <task-dir>/focus.json --complete --json
python -m unittest discover -s tests -v
```

检查器只读指定 JSON，不执行其中的命令或链接。退出码：0 为记录检查通过，1 为需纠偏，2 为结构错误，3 为验收未完成。已满足验收的任务不会因无关的空转历史被迫继续。

测试覆盖无证据通过、空转纠偏、失败实验产生新证据、规则裁决、任务恢复、验收与只读行为；测试不能证明代理在真实长程任务中一定遵循技能。首次实际使用时记录基线，再观察恢复探针通过情况与重复劳动是否下降。

## 上游调研与整合

调研了 [planning-with-files](https://github.com/OthmanAdi/planning-with-files)、[Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)、[superpowers](https://github.com/obra/superpowers) 和 [GSD](https://github.com/gsd-build/get-shit-done)。采用文件状态、规则冲突标注、证据验收和会话恢复机制，并按当前需求重写为中文工作流。

固定版本、具体文件与整合取舍见 [来源记录](skills/focus/references/sources.md)。入口技能见 [SKILL.md](skills/focus/SKILL.md)。
