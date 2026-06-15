# AutoStudy 快速版

> 默认入口：中文完整版见 [README.md](./README.md)。英文完整版见 [README.en.md](./README.en.md)。

AutoStudy 是本地 Canvas LMS 学业助手，已在 HKUST(GZ) 的 Canvas 实例上验证。它跑在 Claude Code / Codex 这类
agent 环境里，帮你同步作业、规划 ddl、侦查作业要求、生成本地草稿、整理课件和课程笔记。

一句话记住：

```text
AutoStudy 先看清 Canvas，再问清你的意图，然后生成你能审核的本地产物。
```

---

## 最常用命令

```text
看看这周有什么作业
```

会生成：

```text
data/sync/current/{courses,assignments,announcements}.json
data/runs/<date>/REPORT.md
data/runs/<date>/plan.json
data/runs/<date>/pending_assignments.json
```

然后你选择编号，AutoStudy 才会进入某个作业。

```text
帮我完成 DSAA2011 Project，先生成本地草稿，不提交
```

会生成单作业工作台：

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
│   └── announcements.json
├── references/
│   ├── REFERENCE_INDEX.md
│   ├── source_docs/
│   └── canvas_native/
│       └── announcement-<id-or-slug>/source.json
├── spec.md
├── investigation/review_a.json
├── investigation/alignment_brief.md
├── pipeline_design.md
├── draft/
├── verification.log
└── result.json
```

```text
同步 DSAA2011 的资料
写 DSAA2011 的课程笔记
```

会使用：

```text
data/courses/<COURSE>/
├── materials/
├── canvas_sync/
└── notes/
```

---

## 第一次使用

AutoStudy 要作为一个独立仓库运行，不是只复制一个 `skill.md`。推荐先在 Claude Code / Codex 里打开一个准备用来放 AutoStudy 的空白项目文件夹，然后说：

```text
请把 https://github.com/Aurorra1123/autoust-dev clone 到当前空白文件夹，
读取里面的 skill.md，并按步骤帮我完成初始化。
```

agent 应该先确认当前目录是空目录，再执行：

```bash
git clone https://github.com/Aurorra1123/autoust-dev.git .
```

如果当前目录不是空的，或当前工作区不明确，agent 应该先问你要放到哪里。不要让它默默默认到 `~/workspace`、桌面或下载目录。

你也可以明确指定一个固定文件夹：

```text
请把 https://github.com/Aurorra1123/autoust-dev clone 到 ~/workspace/autoust-dev，
然后进入这个文件夹，读取里面的 skill.md，并按步骤帮我完成初始化。
```

也可以自己先 clone：

```bash
mkdir -p ~/workspace
git clone https://github.com/Aurorra1123/autoust-dev.git ~/workspace/autoust-dev
cd ~/workspace/autoust-dev
```

然后在这个目录里说：

```text
请使用当前目录里的 AutoStudy skill，阅读 skill.md，然后帮我初始化。
```

Canvas 登录：

```bash
.venv/bin/canvascli init --canvas-url "https://canvas.example.edu"
```

检查登录态：

```bash
.venv/bin/canvascli whoami
```

登录态在本机：

```text
~/Library/Application Support/canvascli/state.json
```

这是 credential，不要打印、复制、提交。

---

## 重要底线

- `sync-status` 只规划，不自动做作业。
- AutoStudy 不会自动提交 Canvas。
- 作业草稿来自 `spec.md + alignment_brief.md + pipeline_design.md`，不是来自标题脑补。
- group 信息、partner 名字、dataset、personal experience、video URL 等必须由用户提供或标记为 human review item。
- 产物都在本地 `data/`，你需要审核后再决定是否提交。

---

## 当前状态

可用：

- Canvas 状态同步和计划生成。
- Canvas-grounded 作业侦查。
- 本地草稿生成和验证日志。
- 课程资料同步。
- 课程笔记生成。

仍在打磨：

- executor/reviewer runtime 的 clean validation。
- 继续/修复已有草稿的体验。
- 课程级/用户级偏好记忆。
- 安全 sandbox 作业上的真实 Canvas submission E2E。
