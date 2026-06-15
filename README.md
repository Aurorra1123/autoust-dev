# AutoStudy

> 本地 Canvas LMS 学业助手 skill，已在 HKUST(GZ) 的 Canvas 实例上验证。
> 同步 Canvas、规划 ddl、侦查作业要求、生成可审核草稿、归档课件、生成课程笔记。

其他版本：

- [English README](./README.en.md)
- [快速版中文 README](./README.quick.md)

AutoStudy 是一个跑在 Claude Code / Codex 这类 agentic coding 环境里的
**本地 Canvas LMS skill 包**，已在 HKUST(GZ) 的 Canvas 实例上验证。你用自然语言提出需求，agent 读取 `skill.md`，调用本地
`canvascli` 数据层，把证据和产物写回这个仓库，并在关键节点询问你。

它不是网页应用，不是托管服务，也不是后台偷偷跑的自动化机器人。它更像一个
学业助手：先收集 Canvas 上的真实上下文，解释它找到了什么，遇到开放性任务时
和你对齐方向，然后生成你可以检查、修改、决定是否提交的本地 artifacts。

---

## 你可以让它做什么

```text
"看看这周有什么作业"
"同步课程状态"
"帮我完成 DSAA2011 Project，先生成本地草稿，不提交"
"继续改上次那个 report，让实验讨论更深入"
"同步 DSAA2011 的课件"
"把 DSAA2011 的 lecture notes 写出来"
```

当前用户侧任务：

| 任务 | 能力 | 产物位置 |
|---|---|---|
| `sync-status` | 同步 Canvas 课程、作业、公告，并生成建议计划。只规划，不自动执行作业。 | `data/runs/<date>/REPORT.md`, `plan.json`, `pending_assignments.json` |
| `do-homework` | 建立单作业工作台，侦查 Canvas 来源，和你对齐意图，动态设计 pipeline，生成本地草稿，最后询问是否提交。 | `data/homework/<COURSE>/<HWID>/` |
| `sync-course` | 按课程归档课件、公告、module 结构，供后续复习和笔记复用。 | `data/courses/<COURSE>/` |
| `write-course-notes` | 从已同步的 lecture PDFs 生成 Obsidian 风格 Markdown 笔记。 | `data/courses/<COURSE>/notes/` |

旧 M3 阶段已经验证过 paper / slides / math / lab 四类真实作业产出。现在的主线是
M3.5+：更深的 Canvas 侦查、明确的用户对齐、动态 pipeline、阶段级审查、可恢复的本地工作台。

---

## 快速开始

### 1. 让 agent 加载这个 skill

AutoStudy 是一个完整的本地仓库，不是单独一个 `skill.md` 文件。第一次使用时，最稳的方式是在 Claude Code / Codex 里先打开一个你准备用来放 AutoStudy 的空白项目文件夹，然后让 agent 直接 clone 到当前目录：

```text
请把 https://github.com/Aurorra1123/autoust-dev clone 到当前空白文件夹，
读取里面的 skill.md，并按步骤帮我完成初始化。
```

agent 应该先确认当前目录是空目录，再执行等价于下面的命令：

```bash
git clone https://github.com/Aurorra1123/autoust-dev.git .
```

如果当前目录不是空的，或者你还没有打开一个明确的项目文件夹，agent 应该先问你要放到哪里，而不是默认放进 `~/workspace`、桌面、下载目录或其他隐式位置。

你也可以明确指定一个路径：

```text
请把 https://github.com/Aurorra1123/autoust-dev clone 到 ~/workspace/autoust-dev，
然后进入这个文件夹，读取里面的 skill.md，并按步骤帮我完成初始化。
```

如果你想自己先 clone，也可以这样做：

```bash
mkdir -p ~/workspace
git clone https://github.com/Aurorra1123/autoust-dev.git ~/workspace/autoust-dev
cd ~/workspace/autoust-dev
```

然后在这个目录里告诉 agent：

```text
请使用当前目录里的 AutoStudy skill，阅读 skill.md，然后帮我初始化。
```

`~/workspace/autoust-dev` 只是一个示例位置，不是默认位置。关键是 AutoStudy 要作为一个独立仓库存在，因为 `.venv/`、`data/`、`scripts/` 和 `sub-skills/` 都会在这个仓库目录下使用。agent 应该读取 `skill.md`，检查环境，并把缺失依赖安装到本地 `.venv/`。

### 2. 完成一次 Canvas 登录

AutoStudy 使用独立的 [`canvascli`](https://github.com/Aurorra1123/canvascli)
作为 Canvas 数据层。第一次使用时，agent 会先确认你的 Canvas 学校/域名或登录页，然后打开浏览器让你完成对应的 Canvas SSO：

```bash
.venv/bin/canvascli init --canvas-url "https://canvas.example.edu"
```

Canvas 登录态保存在本机：

```text
~/Library/Application Support/canvascli/state.json
```

这个文件是 credential。agent 不应该打印、复制到聊天、或提交到 git。检查登录态是否仍可用时，应该运行：

```bash
.venv/bin/canvascli whoami
```

`canvascli init` 是登录/刷新命令，不是健康检查。

### 3. 从同步状态开始

最安全的第一句是：

```text
看看这周有什么作业
```

AutoStudy 会：

1. 拉取 Canvas courses / assignments / announcements；
2. 保存当前 sync 快照到 `data/sync/current/`；
3. 写入当天运行目录 `data/runs/<date>/`；
4. 给出编号的下一步建议；
5. 等你选择是否进入某个作业。

如果你选择某个编号，AutoStudy 会用 `scripts/select_plan_item.py` 解析出准确的
Canvas IDs 和建议 workbench。选中编号后，不应该再靠标题模糊匹配。

---

## 作业流程现在是怎样的

AutoStudy 不会只看作业标题就开始生成。当前 homework contract 是：

```text
Canvas raw snapshots, including canvas/announcements.json
-> references/REFERENCE_INDEX.md
-> references/source_docs/ and references/canvas_native/
-> spec.md
-> investigation/rubric.md and investigation/review_a.json
-> investigation/explore_context.md
-> investigation/alignment_brief.md or repair_plan.md
-> pipeline_design.md or repair_pipeline_design.md
-> stage_briefs/
-> stage_results/ and stage_reviews/
-> draft/
-> verification.log
-> result.json
```

换成普通话就是：

1. **侦查**：通过 `canvascli` 检查 assignment page、rubric、front page、
   syllabus、modules、module items、announcements、files、pages 和外部链接。
2. **保存 reference**：`reference_collector` 把任务相关的原始证据保存到
   `references/`，包括 PDF 三件套和逐条筛选后的
   `references/canvas_native/announcement-<id-or-slug>/source.json`；不会把完整
   `canvas/announcements.json` 整包塞进 `references/canvas_native/`。
3. **写 spec**：主代理读取 `references/REFERENCE_INDEX.md` 和保存好的原始证据，
   把真正的作业要求总结到 `spec.md`，并写 `investigation/review_a.json`。
4. **和你对齐**：只问那些不问就会猜错的问题，例如 topic、group info、dataset、
   architecture、style、scope。
5. **确认 agreement**：新作业写入 `investigation/alignment_brief.md`；继续修改已有草稿时写入 `repair_plan.md`。
6. **设计 pipeline**：根据 spec 和确认后的 intent 写 `pipeline_design.md`。现在不再有固定的 “paper pipeline” 或 “lab pipeline”，而是按作业现场组合工具。
7. **执行和审查**：生成 stage briefs，必要时派发 executor/reviewer，记录 receipts，运行检查，把最终产物放进 `draft/`。
8. **提交前询问**：Canvas submission 从不自动发生。

所以一个复杂项目可以在同一个 workbench 里同时产生 notebook、report PDF、slides、
requirements、source zip、verification log 和 human review items。

---

## 课程资料和笔记

同步课程资料：

```text
同步 DSAA2011 的资料
```

会进入 `sync-course`，确认范围后归档到：

```text
data/courses/<COURSE>/
├── materials/
├── canvas_sync/
├── notes/
├── meta.json
└── index.md
```

然后你可以说：

```text
写 DSAA2011 的课程笔记
```

这会进入 `write-course-notes`，从课程归档里的 lecture PDFs 生成结构化 Markdown notes。

---

## 仓库结构

```text
AutoStudy/
├── skill.md                         # 用户侧 skill 入口和路由
├── README.md                        # 中文默认 README
├── README.en.md                     # 英文完整版
├── README.quick.md                  # 中文快速版
├── scripts/
│   ├── write_scan_plan.py           # Canvas snapshot -> plan/report
│   ├── select_plan_item.py          # 编号计划项 -> 精确 handoff
│   └── write_homework_result.py     # 稳定 result.json writer
├── sub-skills/
│   ├── tasks/
│   │   ├── sync-status.md
│   │   ├── do-homework.md
│   │   ├── task-orchestrator.md
│   │   ├── sync-course.md
│   │   └── write-course-notes.md
│   └── tools/
│       ├── canvascli-setup.md
│       ├── canvascli-api.md
│       ├── assignment-recon.md
│       ├── code-writer.md
│       ├── writing-helper.md
│       ├── pdf-renderer.md
│       ├── slide-maker.md
│       └── ...
├── docs/
│   ├── DEVELOPMENT.md
│   ├── ROADMAP.md
│   ├── COLLABORATION.md
│   ├── runtime-agent-protocol.md
│   ├── skills-architecture-spec.md
│   ├── PITFALLS.md
│   ├── plans/feature-list.json
│   └── progress/agent-progress.md
└── data/                            # 本地 Canvas 快照和产物，gitignored
```

`data/` 是本地工作区，可能包含课程文件、作业草稿、verification logs 和 result receipts。
当前 Canvas sync 快照固定放在 `data/sync/current/`，每次 scan-plan 使用过的副本会放在
`data/runs/<date>/raw/`。

---

## 当前状态

已经可用：

- `canvascli` Canvas 数据层。
- `sync-status` scan-plan 流程。
- `do-homework` workbench、侦查、alignment、动态 pipeline planning。
- `task-orchestrator` 基于已确认 pipeline 的本地草稿执行流。
- M3 工具：prose、code、figures、tests、slides、PDF rendering、humanizer。
- 课程资料同步和课程笔记生成。
- `result.json` 记录 skipped、pipeline_ready、draft_ready、submitted、error 等状态。

仍在 hardening：

- 统一 executor/reviewer runtime 的 clean process validation。
- 保留已有草稿的 repair / continue 体验。
- course-level 和 user-level preference memory。
- 在安全的未过期/sandbox 作业上做一次真实 Canvas submission E2E。
- Claude Code 之外的多 runtime 支持。

详细状态见：

- [docs/ROADMAP.md](./docs/ROADMAP.md)
- [docs/plans/feature-list.json](./docs/plans/feature-list.json)

---

## 安全和学术诚信

- AutoStudy 不会自动提交 Canvas。
- `sync-status` 只给计划，不会自动执行计划项。
- 大范围下载、生成作业草稿、提交文件前都应该有用户确认点。
- AutoStudy 不应该编造 group details、datasets、personal experience、partner names、instructor oral instructions 或不可达来源。
- 草稿是本地 artifacts，必须由你检查、修改、决定是否提交。
- 目标是减少重复劳动、提升可追溯性，而不是替学生隐藏责任。

拿不准时，AutoStudy 应该停下来解释不确定性，而不是猜。

---

## 贡献开发

如果你是开发者，先读 [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)。它解释
AutoStudy 与 `canvascli` 的边界、Canvas Copilot 参考项目、当前分支策略、
progress/backlog 更新规则和验证要求。
