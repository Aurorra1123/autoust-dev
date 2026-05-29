# AutoStudy

> HKUST(GZ) 本科学业自动化 skill
> 同步 Canvas 课程状态 · 下载课件 · 自然语言驱动

---

## 这是什么

AutoStudy 是一个 **skill 包**，让你在 Claude Code（或未来的 Codex / Kimi Code CLI）里用自然语言指挥 agent 处理 HKUST(GZ) 的学业任务：

```
你："看看这周有什么作业？"
agent: 拉 Canvas 数据 → 整理摘要 → 列出 ddl 优先级

你："把 DSAA2043 的 midterm 资料下下来"
agent: 列文件夹 → 询问范围 → 下载到本地
```

设计上参考了 [AutoPku](https://github.com/ICUlizhi/AutoPku) 的"skill 寄生在宿主 agent 上"思路。**没有 npm install、没有自建后端、没有要配的 API key**，全部数据在你本地。

---

## 快速开始

### 第一步：把 skill 扔给 agentic AI

打开 Claude Code（或未来支持的 Codex / Kimi Code），告诉它：

```
下载 https://github.com/Aurorra1123/autoust-dev，并执行这个 skill
```

它会自己 `git clone` 这个仓库、读取 `skill.md`、检测环境、自动装好 canvascli 和 Chromium。

### 第二步：完成一次 SSO 登录

agent 会在合适的时机让你扫码 / 登录学校 SSO（一次性，cookie 持久化在 `~/Library/Application Support/canvascli/`）。这是整个流程里**唯一**需要你动手的步骤。

### 第三步：下达命令

```
"看看这周有什么作业"
"帮我同步课程状态"
"下载 DSAA2043 的 midterm 资料"
"帮我完成 DSAA2043 Lab-Assignment 1"
```

剩下的去做别的，相信 agent。

> 提示：Claude Code 不会主动激活之前加载过的 skill，下次开新会话时你需要再提一句"参考 autoust-dev 这个 skill"。

---

## 它在做什么（透明版）

如果你想知道 agent 在背后跑了什么：

1. **环境检测**：检查当前目录有没有 `.venv/`，`canvascli` 是否能跑、Canvas session 是否有效
2. **首次安装**（缺什么补什么）：
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install "git+https://github.com/Aurorra1123/canvascli"
   .venv/bin/playwright install chromium
   .venv/bin/canvascli init   # ← 你登录的地方
   ```
3. **跑实际任务**：根据你的意图路由到 `sub-skills/tasks/` 下的某个 task spec，由 task spec 调度 `sub-skills/tools/` 下的工具链产出 deliverable

---

## 当前阶段

**MVP（M3 核心）** — 4 个旗舰作业场景（paper / slides / math / lab）已在真实的 HKUST(GZ) Canvas 作业上端到端验证。

已完成：
- ✅ Canvas 抓取器（课程 / 作业 / 公告 / 课件 / Quiz / 讨论）+ 增量下载
- ✅ 主 skill.md + sub-skills 三层架构（runtime/tools/tasks）
- ✅ `tasks/sync-status.md` — 同步状态 + 摘要
- ✅ `tasks/do-homework.md` — 作业端到端（含 problem-extractor 数据接地）
- ✅ `tasks/task-orchestrator.md` — 工具链调度
- ✅ 8 个工具 sub-skill（pdf-renderer / writing-helper / paper-search / figure-maker / code-writer / test-runner / slide-maker / problem-extractor）

下一步：交互式澄清回合、submission 接口验证、多 runtime（Codex / Kimi）。详见 [docs/ROADMAP.md](./docs/ROADMAP.md)。

---

## 仓库结构

```
AutoStudy/
├── skill.md                    # Claude Code 入口（用户侧）
├── AGENTS.md                   # 开发者入口
├── README.md                   # 你正在读的
├── docs/
│   ├── ROADMAP.md              # 分阶段路线图
│   ├── MARKETING.md            # 对外宣发场景
│   ├── PITFALLS.md             # 踩坑记录（重要）
│   ├── AutoStudy.pdf           # 原始设计理念
│   ├── plan.md                 # 项目最初的 brief
│   ├── plans/feature-list.json # 结构化 backlog
│   └── progress/agent-progress.md  # 会话交接日志
├── sub-skills/
│   ├── tools/
│   │   ├── canvascli-setup.md  # 安装外部工具 + 首次登录
│   │   ├── canvascli-api.md    # canvascli 命令手册
│   │   ├── _index.md           # M3 tool 注册表
│   │   └── pdf-renderer.md     # markdown → PDF
│   └── tasks/
│       ├── sync-status.md      # 同步状态任务
│       └── task-orchestrator.md # M3 调度器
└── data/                       # 拉到的 JSON + 下载的文件（gitignored）
```

Canvas 数据层（抓取器）抽出来了 —— 是独立仓库 [`canvascli`](https://github.com/Aurorra1123/canvascli)，MIT 开源。AutoStudy 通过 `pip install "git+https://github.com/Aurorra1123/canvascli"` 一行装到本地 venv 里。
设计思路对应 AutoPku 的 `pku3b`：把数据底座做成可被任何 agent shell out 调用的独立工具。

---

## 与 AutoPku 的关系

[AutoPku](https://github.com/ICUlizhi/AutoPku) 是这个项目的灵感来源。两者的区别：

| | AutoPku | AutoStudy |
|---|---|---|
| 学校 | 北京大学（教学网） | HKUST(GZ)（Canvas） |
| 数据采集 | 依赖外部 CLI `pku3b` | 自己写的 playwright + Canvas REST API |
| 当前覆盖 | 同步通知 / 完成作业 / 写笔记 | 同步状态（更多 task 在 roadmap） |
| 差异化 | Agent Team 全自动完成作业 | 反问式学习 + 设计审核（M3+） |

---

## 安全规则

- 登录态保存在 `.auth/canvas_state.json`（gitignored），**不会上传任何地方**
- 任何下载 / 提交动作前都会用 `AskUserQuestion` 让你确认
- 不会自动选择"最新的"作业或课件
- 不会自动提交作业（M3 加入提交功能时仍会保留确认环节）

---

## 反馈 / 贡献

issue 和 PR 欢迎。先看 [docs/ROADMAP.md](./docs/ROADMAP.md) 了解当前阶段范围。
