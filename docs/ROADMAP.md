# AutoStudy Roadmap

> 目标：把 Canvas 抓取能力 + 学业自动化任务编排，演进成一个能让 HKUST(GZ) 学生在 Claude Code / Codex 上一句话 load 的 skill。
>
> 设计参考：[AutoPku](https://github.com/ICUlizhi/AutoPku) 的三层 sub-skills 架构 + 自然语言驱动。
> 数据底座参考：[pku3b](https://github.com/sshwy/pku3b) 的"独立 CLI + agent shell out"模式。
> 设计理念：见 [AutoStudy.pdf](./AutoStudy.pdf) 的五大模块。
> 对外宣发场景：见 [MARKETING.md](./MARKETING.md)。
> 工程踩坑：见 [PITFALLS.md](./PITFALLS.md)。

---

## 终极形态

用户在 Claude Code 里说一句：

```
clone AutoStudy 仓库 → 执行 skill.md
```

然后用自然语言驱动：

```
"帮我同步这周的作业"
"DSAA2012 第三周的 slides 给我下下来，做一份复习笔记"
"我下周一有几个 ddl，按优先级排一下"
"帮我完成 DLED3020 的 paper critique，做完先给我看草稿"
"用反问式帮我复习 Deep Learning 的 lecture 3"
```

没有 npm install、没有自建 agent 框架、没有要配的 API key —— 全部领域逻辑内嵌在 markdown skill 文件里，吃宿主 agent 的能力。数据采集层是一个独立的 `canvascli` 工具，任何 agent 都能 shell out 调用。

---

## 五个阶段

每个阶段都是**端到端可用**的，不必做完所有阶段才能给人用。

```
M1  Canvas 抓取器 + 抽离成 canvascli   ✅ 已完成
M2  最小可 load skill                  ✅ 已完成
M3  作业辅助 + 启发式调度               ✅ MVP（4 场景已端到端跑通）
M3.5 Canvas Generic 式作业侦查 + 单作业计划  🚧 当前重点
M4  反问式学习助手
M5  多平台 + 主动提醒
```

---

## M1. Canvas 抓取器 + 抽离成 canvascli（✅ 已完成）

**Phase 1 — AutoStudy 内的 scraper**（commit `7e6725e`）：
- `scraper/api.py` — `CanvasClient`（分页、folder_tree）
- `scraper/login.py` — Playwright 一次性 SSO 登录，cookie 持久化
- `scraper/fetch_*.py` — 6 个资源：courses / assignments / announcements / modules / files / quizzes+discussions
- `scraper/download.py` — 按文件夹下载 + `.state/downloads.json` 增量跳过

**Phase 2 — 抽离为独立 `canvascli` 仓库**（commit `90072ac` + canvascli `0385f54`）：

参考 AutoPku/pku3b 的关系模式（一个独立 CLI + skill 仓库 shell out 调用），把数据采集层从 AutoStudy 抽出来，独立 git 仓库 + 独立发版。

**`canvascli` 仓库**（`~/workspace/canvascli/`）：
- typer 平铺顶层命令：`init / version / whoami / courses / assignments / assignment / announcements / files / folders / download / submit`
- **默认 JSON 输出**（区别于 pku3b 的 ANSI 色文本），`--pretty` 才人类可读
- 写死 `hkust-gz.instructure.com`，不做多校适配
- 认证用 Playwright SSO + cookie 持久化（不存明文密码）
- submit 实现 Canvas 三步上传协议（request slot → S3-like upload → POST submission）

**AutoStudy 接轨**：删 `scraper/`，改为依赖外部 canvascli（`pip install -e ../canvascli/`），sub-skills/tools/ 下新增 `canvascli-setup.md` + `canvascli-api.md`。

**验证过的**：6 门当前学期课、36 个作业、~700MB 课件清单、Midterm 文件夹真实下载 + 增量跳过、submit 端到端可调。

---

## M2. 最小可 load skill（✅ 已完成）

**目标**：让别人 clone 仓库 + 装好 canvascli 后，告诉 Claude Code "执行这个 skill"，能跑通一个完整流程：**同步本周作业 + 列出需要关注的事项**。

**已完成的交付物**（commit `7e6725e` + 后续重构）：

```
AutoStudy/
├── skill.md                       # 主入口 + 意图路由 + 安全规则
├── sub-skills/
│   ├── tools/
│   │   ├── canvascli-setup.md     # 装外部工具 + 首次登录
│   │   ├── canvascli-api.md       # canvascli 命令手册
│   │   ├── _index.md              # M3 tool 注册表（M3 落地的）
│   │   └── pdf-renderer.md        # markdown → PDF（M3 落地的）
│   └── tasks/
│       ├── sync-status.md         # M2 旗舰任务
│       └── task-orchestrator.md   # M3 调度器（M3 落地的）
└── data/                          # 拉到的 JSON + 下载文件（gitignored）
```

**验证过的能力**：
- 陌生 agent 看 skill.md 能正确触发 sync-status
- 自然语言"帮我同步这周作业"输出干净的 5 段式 markdown 摘要
- 30 天阈值过滤掉历史学期残留 overdue
- 安全规则被遵守：不自动下载、不回显 cookie、底部用 AskUserQuestion 引导次级动作
- 中英混合输出 + 课程名缩短 + 链接 markdown 化（agent 自主行为，超预期）

**M2 期间真实暴露的工程问题**（已回灌到文档）：
- Claude Code `!` bash 通道无 TTY，`input()` 立刻 EOF，`/dev/tty` 也不可用
- Python tuple `(datetime, dict)` 排序在 dt 相同时 TypeError
- "overdue" 不能无脑列全历史，加 30 天阈值
- `canvascli version` 是子命令而非 `--version` flag

---

## M3. 作业辅助 + 启发式调度（✅ MVP 已达成）

**目标**：从"看到信息"升级到"产出材料"。引入**启发式 skill 调度**作为元能力 —— agent 看任务画像 + 可用 tool 清单，自己挑工具组合完成异构产出（report / presentation / 题集 / 代码 / 视频...）。

**MVP 验收（2026-05-24 达成）**：4 个旗舰场景在真实 HKUST(GZ) Canvas 作业上跑通，每个都产出真实可交付物。video 场景由独立 video skill 实现，不在 AutoStudy 仓库范围。

| 场景 | 真实作业 | 交付物 | 状态 |
|---|---|---|---|
| paper | DLED3020 Paper Critique | `final.pdf` 45,684 B / 3 pp | ✅ |
| slides | UCUG1077 Group presentation | beamer `slides.pdf` 82,370 B + guizang `slides_guizang.pdf` 1.67 MB / 10 pp | ✅ |
| math | DSAA2043 Lab-Assignment 1 | `solution.pdf` 49,390 B | ✅ |
| lab | DSAA2012 Project Report | `report.pdf` 43,553 B + 14/14 pytest passing | ✅ |
| video | (out of scope) | 留给独立 video skill | ⏸ |

### M3 的三层架构（已落地骨架）

```
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Task                                            │
│   tasks/do-homework.md   tasks/write-notes.md            │
│   tasks/weekly-plan.md                                   │
└──────────┬──────────────────────────────────────────────┘
           │ 调用
           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Orchestrator                       ✅ 骨架已写  │
│   tasks/task-orchestrator.md                             │
│     · 任务类型识别                                       │
│     · 读 tools/_index.md 匹配能力                        │
│     · 启发式 skill 组合 + 调用顺序                       │
└──────────┬──────────────────────────────────────────────┘
           │ 调用
           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 0: Tools (全部 markdown spec + 内嵌代码)            │
│   tools/_index.md           ✅ 已写（7 个 tool + 场景表） │
│   tools/pdf-renderer.md     ✅ 已写（tectonic 两步法）   │
│   tools/writing-helper.md   ✅ 已写（essay/report/refl）  │
│   tools/paper-search.md     ✅ 已写（arxiv → bib）        │
│   tools/figure-maker.md     ✅ 已写（matplotlib 三型）    │
│   tools/code-writer.md      ✅ 已写（src + tests）        │
│   tools/test-runner.md      ✅ 已写（pytest 报告）        │
│   tools/slide-maker.md      ✅ 已写（guizang 默认 + beamer fallback）│
│   tools/video-maker.md      ⏸ 由独立 video skill 实现   │
└─────────────────────────────────────────────────────────┘
```

**端到端通路已验证**（commit `37b7daf`）：任务画像 → orchestrator 读 `_index.md` → 匹配 `render_pdf` → pdf-renderer 两步法 → 真 PDF 落盘 + magic bytes 校验。

### `do-homework.md` 软交互流程（M3.5 正在升级）

不是每步都卡用户，**只两个询问点**：

```
用户："帮我完成 DSAA2043 hw3"
  ↓
[A] 解析用户选择或 plan item → 建单作业 workbench
    → Canvas Generic Stage 1-5 侦查
    → 写 spec.md / rubric.md / references/ / review_a.json / pipeline_design.md 第一行
  ↓
[B] ★ 询问点 1：摘要 + 询问意图
       汇报：主 spec 来源、交付物、rubric、不可达资源、output mode
       AskUserQuestion: [继续完整做 / 我有补充 / 只做某范围 / 先不做]
  ↓
[C] 用户同意 → do-homework 完成 pipeline_design.md
       不写 task_profile.yaml
  ↓
[D] task-orchestrator 执行 pipeline_design.md
       tools 读 spec.md + references/ + rubric + 用户补充
       写 draft/、verification_checklist.md、verification.log
  ↓
[E] ★ 询问点 2：提交确认
       AskUserQuestion: [canvascli submit Canvas / 我先看草稿 / 取消]
  ↓
[F] 用户确认 → `canvascli submit <id> <file> --course-id <cid>`
```

### M3 第一个可演示子集：Report 流水线

M3 不可能一口气把所有产出能力做完。首发选 **Report** 类作业（最常见、价值高、风险低）：

**目标场景**：
- DLED3020 Paper Critique（学术批判性 essay）
- UCUG1809 Reflective Essay（反思性写作）

**首发内置 tools**：
| Tool | 能力 | 状态 |
|---|---|---|
| `tools/_index.md` | 可用 tool 清单 + verb 词表 | ✅ |
| `tools/pdf-renderer.md` | Markdown → PDF（pandoc + tectonic，中文 + LaTeX 数学 + callout） | ✅ |
| `tools/paper-search.md` | 文献搜索（arxiv API / Google Scholar 链接生成） | 待写 |
| `tools/figure-maker.md` | 数据可视化（matplotlib 代码生成 + 渲染） | 待写 |
| `tools/writing-helper.md` | essay 结构化生成（intro / body / conclusion，引用格式 APA / IEEE） | 待写 |

**端到端验收**：
- [ ] 用户说"帮我完成 DLED3020 Assessment Task 3 (Paper Critique)"
- [ ] agent 用 canvascli 拉作业 description + rubric
- [ ] 识别为 report 类，summary 给用户确认
- [ ] orchestrator 调度：paper-search → writing-helper → pdf-renderer → PDF
- [ ] 用户审核后通过 `canvascli submit` 提交（或本地保存）
- [ ] 全程只有 [B][E] 两个 AskUserQuestion

### 后续场景（M3 内逐步加）

完成 Report 后再加 tools 支持其他场景。详细的对外宣发场景规划见 [MARKETING.md](./MARKETING.md)，按打磨成本 vs 宣传效果排序：

| 优先级 | 场景 | 新增 tool | 示例作业 |
|---|---|---|---|
| 1 (首发) | **写论文 / Report** | 见上表 | DLED3020 paper critique |
| 2 | **数学作业 (LaTeX + PDF)** | `tools/proof-solver.md` + `tools/math-renderer.md` | DSAA2043 证明题 |
| 3 | **Lab 代码自动完成** | `tools/code-writer.md` + `tools/test-runner.md` | DSAA2012 deep learning lab |
| 4 | **PPT / Presentation** | `tools/slide-maker.md` (marp / reveal-md / pptx) | UCUG1077 group presentation |
| 5 (留作宣传重磅) | **视频剪辑 / 多模态** | `tools/video-maker.md` (ffmpeg + manim + whisper) | lecture summary / project demo |

每加一个 tool，orchestrator 自动获得新能力 —— 因为它读的是 `tools/_index.md`，不写死类型。

**视频场景延后理由**：技术栈最复杂（ffmpeg + manim + whisper），但宣传效果最爆炸。在前 4 个场景稳定后才开工。

### 第三方链接（OJ / 外部表单）处理原则

**默认路径（推荐）**：让学生把题目内容存到本地，agent 在本地完成解题，输出给学生手动复制粘贴。

**可选路径（需用户明确同意）**：playwright 模拟浏览器操作。涉及未知站点的认证、风控、合规风险，skill 提示时必须明确"不推荐"。

### Canvas API 自动提交

`canvascli submit` 已实现 Canvas 三步上传协议，**M3 可以直接用**：
- 不自动选择最新作业（必须用户在 [B] 明确指定）
- 提交前必须 [E] 确认
- 失败时清晰提示，不重试
- 实测有效性留到第一个真实 do-homework 跑通时验证

### 设计要点

- **不假设"全部代写"**：[B] 给用户"只做某几题"的选项，尊重学生想自己做部分的需求
- **产物沉淀本地**：每份草稿存到 `data/homework/<course>/<hw>/`，不是丢在 chat session
- **群组作业拒绝代做**：识别到 group 类型时主动告知"涉及组员协作，不适合 agent 全权代做"
- **Tool 之间用文件传递**：orchestrator 不把 tool 当函数调用，而是把中间产物落地到 `data/homework/.../intermediate/`，每个 tool 读写文件。这样：
  - tool 单独可测试
  - 失败可断点续跑
  - 用户可以中途接管某一步

### M3 当前剩余工作（按推荐顺序）

1. ✅ `tools/_index.md`（能力清单）
2. ✅ `tools/pdf-renderer.md`（最稳的纯工具）
3. ✅ `tasks/task-orchestrator.md`（调度器骨架）
4. ✅ `tasks/do-homework.md`（端到端 task）
5. ✅ `tools/writing-helper.md`（让 [D] 草稿真有质量）
6. ✅ `tools/paper-search.md`
7. ✅ `tools/figure-maker.md`
8. ✅ `tools/code-writer.md` + `tools/test-runner.md`
9. ✅ `tools/slide-maker.md`（guizang 默认 + beamer fallback）
10. ✅ Report / slides / math / lab 4 个场景在真实作业上跑通
11. ⏸ M3-SUBMIT：`canvascli submit` 在真实未过期作业上端到端验证（当前代码层已验，需 sandbox 作业补一次真实回归）

---

## M3.5. Canvas Generic 式作业侦查 + 单作业计划（✅ 基础验证通过）

**目标**：把 M3 的"能产出"升级为"先稳定理解作业，再按真实 spec 现场设计执行计划"。这一阶段大量参考 Canvas Copilot，但保留 AutoStudy 的助手式用户循环。

### 已完成 / 已对齐

- `canvascli` 数据层已经补齐 Copilot 式原子命令：`assignment`、`rubric`、`front-page`、`syllabus`、`modules`、`module-items`、`page`、`file`、`assignment-files`；不使用 `assignment-context` 聚合命令。
- `sync-status` 已升级为 scan-plan：写 `data/runs/<today>/pending_assignments.json`、`plan.json`、`REPORT.md`，只建议下一步，不自动执行作业。
- `scripts/select_plan_item.py` 已作为 numbered plan item 到单作业 workbench 的稳定 handoff。
- 单作业 workbench 结构已确定：`canvas/`、`spec.md`、`references/`、`investigation/`、`pipeline_design.md`、`draft/`、`verification_checklist.md`、`verification.log`、`result.json`。
- `result.json` 已作为 do-homework 的状态收据；`review_a.json` 只表示侦查是否足够。
- DSAA2011 Project 与 UCUG1505 FINAL project 已按 agent-led Canvas Generic Stage 1-5 跑通到 `pipeline_design.md` 和 task-orchestrator dry-run。

### 当前批准方向

正式侦查流程完全参考 Canvas Copilot `canvas-generic` Stage 1-5，但通过 `canvascli` 原子命令实现：

```text
Stage 1 fetch-context
  read assignment / front page / modules / syllabus / attached files / external URLs
  write standardized spec.md

Stage 2 find-rubric
  search Canvas rubric, spec, PDFs, modules, syllabus, external URLs
  write investigation/rubric.md

Stage 3 locate-inputs
  fetch PDFs, Google Docs, starter code, datasets, external text
  write references/ and investigation/unreachable.txt

Stage 4 review investigation
  reviewer/sub-agent if available; otherwise cold self-review
  read spec.md + rubric.md + references/ + unreachable.txt
  write investigation/review_a.json

Stage 5 classify-output
  choose doc_prose / pdf_annotated / pdf_typed / code / form_answers / slides / mixed
  start pipeline_design.md
```

`scripts/recon_assignment.py` 是历史过渡验证，不是正式 do-homework 路径。正式路径由 agent 逐源阅读并写 `spec.md`；机械脚本最多只能辅助保存 JSON 或下载单个文件，不能替 agent 判断主 spec、写最终 spec、写 review_a 或分类 output mode。

### 已完成验收

已用两个真实 case 验证新 flow，不只是文档演练：

- **DSAA2011 Project**：assignment 页面为空，真正 spec 在 module PDF；`pipeline_design.md` 识别 `mixed`，包含 notebook/code、report PDF、presentation PDF、requirements、可选 data/package；dry-run 正确停在 group/dataset/style-file blockers。
- **UCUG1505 FINAL project**：assignment page 与 Week 4 module 指向同一个 Google Doc spec，Week 9 slides 是支持上下文；`pipeline_design.md` 识别 `mixed`，包含 code/source zip、documentation、video demo 相关 human review item；dry-run 正确停在 partner/concept/code/video blockers。

通过标准已满足：`spec.md` 能清楚说明主 spec 和交付物，`review_a.json.verdict == "proceed"`，`pipeline_design.md` 可被 task-orchestrator dry-run 读取并返回 human blockers，且工具不再需要 `task_profile.yaml`。

### 后续开发重点

- 把 do-homework `[B]` 的侦查汇报和用户补充问题做得更顺：直接把 DSAA/UCUG 这种 blockers 转成用户可理解的问题。
- 让 task-orchestrator 对 `pipeline_design.md` 的执行结果有更稳定的 structured summary，区分 `success` / `partial` / `failed_due_to_human_blocker`。
- 在用户补齐 DSAA group/dataset/style-file 或 UCUG partner/concept/video/code 信息后，跑一次真正 draft generation，而不是只做 dry-run。
- **Skills 架构落地**（详见 `docs/skills-architecture-spec.md`）：重构 code-writer / writing-helper 为渐进式加载模式，新建语言附录和 humanizer skill，在真实 mixed 任务上验证新架构。

### 设计理念（M3.5+ 长期方向）

以下五条设计理念指导 M3.5 及后续所有开发。这些原则来自对 Canvas Copilot 的深度参考，但服务于 AutoStudy 的助手式定位：

#### 1. 助手式，不是自动化

Canvas Copilot 是"scan → batch plan → approval → batch execute → report"的自动化系统。AutoStudy 是"用户说一句话，agent 在环理解、侦查、汇报、确认、执行、审查"的助手。借鉴 Copilot 的成熟机制（原子数据访问、逐源侦查、结构化状态），但每次交互都保留用户的选择权和知情权。

#### 2. 动态 skills 组合，不绑固定 pipeline

MVP 阶段的固定流水线（paper → search + write + render）验证了单个 tool 的可靠性，但复杂/混合任务（如"论文搜索 + 代码分析 + report 撰写 + PPT 构造"）无法靠固定链完成好。AutoStudy 的方向是：充分发挥 Claude Code 的 agent 能力，`pipeline_design.md` 由 agent 根据侦查结果现场设计，`_index.md` 是按需加载的 skills 注册表而非固定路由表。输出模式（doc_prose / pdf_typed / code / slides / mixed）也不应是预设 pipeline，而是 skills 的按需组合——后续可以考虑将输出模式本身也设计为可加载的 skill。

#### 3. 多轮迭代：单轮中断恢复 + 跨轮次持续优化

复杂任务在一个会话中大概率做不好。AutoStudy 的设计必须同时考虑：

- **单轮内的中断恢复**：如果会话中途 context 溢出或 agent 中断，`result.json` + workbench 文件结构允许下一个 session 从断点继续。
- **跨轮次的迭代优化**：一轮做完后用户不满意（草稿质量不够、某个部分需要重做、新信息需要补充），应该能从已有 workbench 继续迭代，而不是从零开始。`result.json` 的状态不只是 `draft_ready` / `submitted`，还要支持 `revision_needed`，pipeline 中每个阶段的产物都应可追溯和可重做。

这是 AutoStudy 与 Canvas Copilot 的关键差异：Copilot 的目标是"一次性走完 pipeline"，AutoStudy 的目标是"长期陪伴用户打磨交付物"。

#### 4. 三层偏好体系

用户偏好不应该每次都从零采集。AutoStudy 设计三层偏好沉淀：

| 层级 | 采集时机 | 存储位置 | 生命周期 |
|---|---|---|---|
| **任务级** | do-homework `[B]` 用户补充环节 | `investigation/user_notes.md` / `investigation/user_scope.md` | 单次作业 |
| **课程级** | 首次作业侦查后积累，后续作业自动读取 | `data/course-overrides/<COURSE>.md` 或 workbench overlay | 学期内持续 |
| **用户级** | 用户主动声明或 agent 从交互中推断 | Claude Code 项目级 memory（`~/.claude/projects/.../memory/`） | 跨学期持久 |

任务级偏好是最基础的——用户在 `[B]` 补充的组队信息、口头要求、选题方向等。课程级偏好是进阶——如果某门课教授"始终要求 2000 字"、"偏好 PDF 格式"、"作业 spec 总是在 module 里"，这些不需要每次强调。用户级偏好最持久——借助 Claude Code 的 memory 能力，可以存储"我喜欢中文输出"、"我的代码风格偏好"等跨课程的个人偏好。

Canvas Copilot 用 per-cluster learnings overlay 文件实现类似功能，但它的 overlay 是纯机器累积的。AutoStudy 的三层设计更灵活，因为中间层可以借助 agent 的理解力做"课程习惯推断"，而不只是机械记录。

#### 5. 审查前置：尽可能多的子代理审查点

参考 Canvas Copilot 的 3 个 sub-agent 审查机制（A: 调查完整性 / B: 验证清单设计 / C: 验证覆盖度），AutoStudy 的设计理念是：

- **侦查阶段**：Sub-agent A 审查 `spec.md` + `rubric.md` + `references/` 的完整性（已实现为 cold self-review，后续升级为独立 sub-agent）。
- **管线设计阶段**：审查 `pipeline_design.md` 的合理性——交付物是否覆盖 spec 要求、skills 选择是否充分、遗漏了什么。
- **生成阶段**：每个 pipeline stage 完成后，可以插入子代理审查 + 验收清单。例如 code-writer 完成后审查代码质量，writing-helper 完成后审查论述结构。这不是固定审查，而是 `pipeline_design.md` 中每个阶段都可以声明"此阶段完成后需要审查"和对应的审查要点。
- **验证阶段**：Sub-agent B 从 rubric 设计可量化的验证清单，Sub-agent C 审查验证覆盖度（防止 false-pass）。

核心原则：pipeline 中每完成一个原子阶段，都可以选择加一个子代理审查。审查点不是固定的，而是在 `pipeline_design.md` 中按需声明。这样既保证了审查的完备性，又不强制每个阶段都审查（有些阶段足够简单，审查成本大于收益）。

---

## M4. 反问式学习助手

**目标**：实现 AutoStudy.pdf 里最有差异化的模块 —— Interactive Tutor。这是 AutoPku **没有**的部分。

### 核心机制

```
1. Agent 读用户笔记 / slides，提取知识点
2. 用 Socratic questioning 反问用户
3. 根据答案判断掌握程度，hint 而非给完整答案
4. 把"掌握程度"写到 data/mastery/<course>.json
5. 下次复习时优先攻薄弱点
```

### 新增 tasks

| Task | 触发例句 |
|---|---|
| `tutor-session.md` | "考前 mock 一下 DSAA2043" |
| `weakness-review.md` | "把我之前弱的点再过一遍" |

### 新增数据层

```
data/mastery/
├── DSAA2043.json    # { "二叉搜索树平衡": {"confidence": 0.4, "last_seen": "2026-05-10"}, ... }
└── ...
```

### 设计要点

- **掌握程度是持久化的**：跨 session 累积，不是单次对话
- **提示梯度**：Socratic → hint → 部分解 → 完整解，agent 根据答错次数递进
- **不给完整答案是默认行为**（写进 SKILL.md 的 safety section）
- **可复用 M3 orchestrator**："按这门课的薄弱点生成一套复习材料" → flashcards + mock_questions 多 tool 组合

---

## M5. 多平台 + 主动提醒

**目标**：覆盖完整的 5 模块、打通跨 agent 平台、引入主动性。

### M5a 多 runtime 适配

参考 AutoPku 的 `sub-skills/runtime/`：
- `claude-team.md` — Agent Team 并行
- `codex-subagent.md` — Codex native subagents
- `kimi-team.md` — Kimi Code CLI

每门课的资源拉取并行化（6 个 agents 同时跑），从串行 30s → 并行 5s。

**注意**：canvascli 本身已经天然支持跨 agent —— 任何能 shell out 的 agent 都能调它。这一阶段主要是 sub-agent 派生方式的差异适配，不是数据层差异。

### M5b 主动提醒（Proactive Reminder）

这是 PDF 里强调的"区别普通 Web Chat 的关键"。技术路径：

- 用 Claude Code 的 **hooks** 机制配置 cron-like 触发
- 例如 `SessionStart` hook 检查 ddl，距离 < 48h 的高亮提醒
- 或用 `CronCreate` 工具创建定时任务（每天早上 9 点检查 ddl）

---

## 跨阶段的几个原则

### 1. 安全边界从 M2 开始就立起来

- 不回显登录态（cookie 不入 git，不打印到 stdout）
- 下载、提交、外发任何操作前都用 `AskUserQuestion` 确认
- 不自动选择"最新"的作业 / 课件 / 公告
- canvascli 自身保持中立（不强制 confirm），confirm 责任落在 skill 层

### 2. 踩坑回灌

每次实战发现的问题（PDF 渲染、cookie 过期、特殊字符路径、tuple 排序、typer 子命令 vs flag）都写回对应的 sub-skill 文件 + PITFALLS.md，让下次执行的 agent 直接绕开。这是 AutoPku 第十一阶段的核心经验。

### 3. 单体先 → 抽象后

不要一开始就上多层架构。M2 阶段单体 scraper，M2 结束后才抽出 canvascli。三层 orchestrator 也是先有一个 tool 跑通再补结构。这条原则在 canvascli 抽离时被现实验证 —— 它**确实是在第一次需要"被外部 agent 调用"时才出现的合理需求**，不是预先设计的。

### 4. 端到端 > 完整

宁可一个 task 跑通端到端，也不要五个 task 各完成 80%。M2 验收标准里"陌生用户能跑通"比"功能多"重要；M3 同理，先 Report 一个场景跑完整链路（含 submit），再扩到其他场景。

### 5. 数据采集和 skill 调度分离

- **数据采集层**（canvascli）：独立仓库、独立发版、JSON-by-default、任何 agent 可 shell out
- **skill 调度层**（AutoStudy）：纯 markdown，吃宿主 agent 能力，不养独立 Python 服务
- 唯一例外是 canvascli 这一个 Python 包，它扮演"AutoPku 的 pku3b"角色

---

## 不在 roadmap 里的事

明确**不做**的：

- ❌ 自建 Web UI / 桌面应用 — 完全寄生在 Claude Code / Codex 上
- ❌ 自建后端服务 / 数据库 — 数据全部本地文件
- ❌ 多用户协同 / 班级共享 — 单人本地工具
- ❌ Notion / Obsidian 双向同步 — 留给用户自己用文件系统接
- ❌ 自动注册账号 / 选课操作 — 风险太高、价值不高
- ❌ canvascli 多校适配 — 写死 HKUST(GZ)，其他校如果想用自己 fork

---

## 当前位置

```
[M1 ✅] ──→ [M2 ✅] ──→ [M3 ✅ MVP] ──→ [M4] ──→ [M5]
                          ↑
                       4 场景已端到端
```

**最近 commit**：

```
canvascli 仓库            AutoStudy 仓库
─────────────────────    ──────────────────────────
0385f54 Initial          (next) feat: MVP — 4 flagship scenarios E2E
                         d3cd323 adopt harness-best-practice light slice
                         9964365 Rewrite ROADMAP
                         90072ac extract scraper to canvascli
                         37b7daf M3 foundation
                         7e6725e M2 lockdown
```

**M3 MVP 已完成**：
- 三层架构骨架 + 7 个 tool（pdf-renderer / writing-helper / paper-search / figure-maker / code-writer / test-runner / slide-maker）
- `do-homework.md` 端到端流程，只在 `[B][E]` 两点交互
- 4 个旗舰场景在真实 HKUST(GZ) 作业上跑通：paper (DLED3020) / slides (UCUG1077, 双路径) / math (DSAA2043) / lab (DSAA2012)
- guizang-ppt-skill 集成为 slides 默认路径，beamer 保留为 fallback
- `canvascli submit` 代码路径完整（待真实 sandbox 作业最终回归）

**M3 收尾**（小，可同 M4 一起做）：
1. 用户提供未过期 / sandbox 作业 → 跑一次真实 `canvascli submit` → 翻 M3-SUBMIT 到 passing

**M3.5+ 长期方向**：
1. 把生成和验证闭环做鲁棒（动态 skills 组合、多轮迭代、阶段级审查）
2. 建立三层偏好体系（任务级 / 课程级 / 用户级）
3. 在真实作业上跑通完整 do-homework flow（侦查 → 用户补充 → 动态管线设计 → 生成 → 审查 → 迭代）
4. 输出模式按需 skills 化（doc_prose / pdf_typed / code / slides 等不再是预设 pipeline，而是可加载的 skill 组合）
