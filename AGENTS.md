# focus 仓库维护约定

- 技能源文件位于 skills/focus；本地安装副本不是第二套设计来源。
- SKILL.md 只保存触发条件、决策与执行主线，条件性细节放 references。
- 本仓库只同步可复用技能；不提交用户项目的任务检查点、聊天记录、密钥或实验数据。
- 修改检查器后运行 Python unittest；技能变化后运行 skill-creator 的 quick_validate.py，并核对实际行为与用户意图。
- 同步前检查 git diff 与暂存文件列表；只提交本次技能文件，不强制推送或改写远端历史。
- Windows 子进程通过 Node windowsHide: true 或 Python CREATE_NO_WINDOW 静默运行；PowerShell 使用 -NoProfile -NonInteractive -WindowStyle Hidden。显式请求的交互终端按用户意图保留。
