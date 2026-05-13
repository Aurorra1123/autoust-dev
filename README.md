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

### 1. Clone 仓库

```bash
git clone https://github.com/<your-org>/AutoStudy.git
cd AutoStudy
```

### 2. 装外部工具 canvascli

Canvas 数据层是独立的 CLI 工具：

```bash
git clone https://github.com/<your-org>/canvascli.git ~/workspace/canvascli
python3 -m venv .venv
.venv/bin/pip install -e ~/workspace/canvascli
.venv/bin/playwright install chromium
.venv/bin/canvascli init   # 一次性 SSO 登录
```

### 3. 让 Claude Code 加载这个 skill

在 Claude Code 里告诉它：

```
执行这个 skill: ./skill.md
```

agent 会读取 `skill.md`，了解项目结构和能力清单。

### 4. 用自然语言下达任务

```
"帮我同步课程状态"
"看看这周有什么作业"
"下载 DSAA2043 的 Midterm 资料"
```

首次使用时，agent 会引导你完成 SSO 登录（只需一次，cookie 持久化）。

---

## 当前阶段

**M2** — 最小可 load skill。已完成：
- ✅ Canvas 抓取器（课程 / 作业 / 公告 / 课件 / Quiz / 讨论）
- ✅ 按文件夹下载 + 增量跳过
- ✅ 主 skill.md + sub-skills 三层架构（runtime/tools/tasks）
- ✅ `tasks/sync-status.md` — 同步状态 + 摘要

下一步（M3）：笔记生成、作业辅助（含设计审核环节）。详见 [ROADMAP.md](./ROADMAP.md)。

---

## 仓库结构

```
AutoStudy/
├── skill.md                    # Claude Code 入口
├── README.md                   # 你正在读的
├── ROADMAP.md                  # 分阶段路线图
├── MARKETING.md                # 对外宣发场景
├── PITFALLS.md                 # 踩坑记录（重要）
├── AutoStudy.pdf               # 原始设计理念
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

Canvas 数据层（抓取器）抽出来了 —— 是独立仓库 [`canvascli`](https://github.com/<your-org>/canvascli)。
通过 `.venv/bin/pip install -e ~/workspace/canvascli` 装到 AutoStudy 的 venv 里。
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

issue 和 PR 欢迎。先看 [ROADMAP.md](./ROADMAP.md) 了解当前阶段范围。
