# AutoStudy Roadmap

> 目标：把今天的 Canvas 抓取器，演进成一个能让 HKUST(GZ) 学生在 Claude Code / Codex 上一键 load 的 skill。
>
> 设计参考：[AutoPku](https://github.com/ICUlizhi/AutoPku) 的三层 sub-skills 架构 + 自然语言驱动。
> 设计理念：见 [AutoStudy.pdf](./AutoStudy.pdf) 的五大模块。
> 工程踩坑：见 [PITFALLS.md](./PITFALLS.md)。

---

## 终极形态

用户在 Claude Code 里说一句：

```
下载 https://github.com/<我们>/AutoStudy，并执行这个 skill
```

然后用自然语言驱动：

```
"帮我同步这周的作业"
"DSAA2012 第三周的 slides 给我下下来，做一份复习笔记"
"我下周一有几个 ddl，按优先级排一下"
"用反问式帮我复习 Deep Learning 的 lecture 3"
```

没有 npm install，没有自建 agent 框架，没有要配的 API key —— 全部领域逻辑内嵌在 skill 文件里，吃宿主 agent 的能力。

---

## 五个阶段

每个阶段都是**端到端可用**的，不是必须做完所有阶段才能给人用。

```
M1  抓取器固化              ✅ 已完成（今天做的）
M2  最小可 load skill       🎯 下一步
M3  学习材料 + 作业辅助
M4  反问式学习助手
M5  多平台 + 主动提醒
```

---

## M1. 抓取器固化（DONE）

**已完成的：**
- `scraper/api.py` — CanvasClient（分页 + folder_tree）
- `scraper/login.py` — 一次性 SSO 登录，cookie 持久化
- `scraper/fetch_courses.py` — 课程 + 作业
- `scraper/fetch_announcements.py` — 公告
- `scraper/fetch_modules.py` — 课件结构
- `scraper/fetch_files.py` — 附件清单
- `scraper/fetch_quizzes_discussions.py` — Quiz + 讨论
- `scraper/download.py` — 按 folder 下载 + 状态管理 + 增量跳过

**验证过的：** 6 门当前学期课程、36 个作业、~700MB 课件清单。Midterm 文件夹真实下载 + 增量跳过工作。

---

## M2. 最小可 load skill 🎯

**目标**：让别人 clone 这个仓库后，告诉 Claude Code "执行这个 skill"，能跑通**一个**完整流程：**同步本周作业 + 列出需要关注的事项**。

### 交付物

```
AutoStudy/
├── skill.md                   # Claude Code 入口（< 100 行，意图路由）
├── codex/autostudy/SKILL.md   # Codex 入口
└── sub-skills/
    ├── runtime/
    │   ├── _detect.md             # 抄 AutoPku
    │   └── create-agent.md        # 抄 AutoPku
    ├── tools/
    │   ├── scraper-setup.md       # venv + playwright + login 流程
    │   ├── scraper-api.md         # 如何调用 scraper/*.py（参数、输出格式）
    │   └── pdf-reader.md          # 抄 AutoPku
    └── tasks/
        └── sync-status.md         # 第一个 task：同步状态 + 摘要
```

### "同步状态"流程长这样

```
用户："看看这周有什么作业"
  ↓
skill 路由到 tasks/sync-status.md
  ↓
Step 1: 检查 .auth/canvas_state.json
        缺失 → 引导用户跑 login.py
        过期 → 引导重新登录
Step 2: Bash 调用 scraper/fetch_courses.py + fetch_announcements.py
Step 3: 读 data/*.json，做语义摘要
Step 4: 用 AskUserQuestion 确认要不要拉课件、要不要下载
Step 5: 输出 markdown 摘要：
        - 本周 ddl 列表（按时间排序）
        - 新公告（如有）
        - 建议关注的事项（评分占比高 + 临近的）
```

### 验收标准

- [ ] 一个**陌生用户** clone 仓库后跟着 skill.md 的指引能跑通登录
- [ ] 自然语言 "帮我同步这周的作业" 触发完整流程
- [ ] 输出的 markdown 摘要本身有用（不是原始数据 dump）
- [ ] 安全规则：不自动下载、不回显 cookie、确认点用 AskUserQuestion

### 风险点

1. **跨平台 runtime 检测**：先只保证 Claude Code 跑通，Codex / Kimi 留到 M5
2. **cookie 过期**：M2 阶段允许"过期就让用户重跑 login.py"，不做自动刷新
3. **scraper 包结构**：M2 阶段需要把 `scraper/` 正式打包（加 `__init__.py`），统一用 `python -m scraper.xxx` 调用

---

## M3. 学习材料 + 作业辅助 + 启发式调度

**目标**：从"看到信息"升级到"产出材料"。引入**启发式 skill 调度**作为元能力 —— agent 看任务画像 + 可用 skill 清单，自己挑工具组合完成异构产出（report / presentation / 题集 / 代码 / 视频...）。

### M3 的两个层次

```
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Task                                            │
│   tasks/do-homework.md   tasks/write-notes.md            │
│   tasks/weekly-plan.md                                   │
└──────────┬──────────────────────────────────────────────┘
           │ 调用
           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Orchestrator (M3 核心新机制)                    │
│   tasks/task-orchestrator.md                             │
│     · 任务类型识别                                       │
│     · 可用 skill 清单维护                                │
│     · 启发式 skill 组合 + 调用顺序                       │
└──────────┬──────────────────────────────────────────────┘
           │ 调用
           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 0: Tools (全部内置)                                │
│   tools/paper-search.md       tools/figure-maker.md      │
│   tools/pdf-renderer.md       tools/slide-maker.md       │
│   tools/writing-helper.md     tools/proof-solver.md      │
│   tools/code-writer.md        ...                        │
└─────────────────────────────────────────────────────────┘
```

### tasks/task-orchestrator.md 设计

**输入**：作业的描述 + 类型 hint + 用户的额外要求

**输出**：一份执行计划（哪些 tool / 什么顺序 / 中间产物路径）+ 实际执行

**核心机制**：

```
1. 任务画像
   读取作业描述 + 评分标准 + 提交格式要求
   输出：{type, deliverables, required_capabilities, deadline, scope}

2. 能力匹配
   读 tools/_index.md（所有内置 tool 的能力清单）
   匹配：required_capabilities → [tool1, tool2, ...]

3. 计划编排
   决定调用顺序、中间产物如何流转
   例（report 类）：
     paper-search → figure-maker (并行) → writing-helper → pdf-renderer
   例（presentation 类）：
     paper-search → figure-maker → slide-maker → 渲染 PDF/PPTX

4. 执行
   逐个 tool 调用，把中间产物存到 data/homework/<course>/<hw>/
   每个 tool 失败时清晰报告，不无脑重试

5. 验收
   产物完整性自检（页数、文件大小、必填章节）
   提交前 AskUserQuestion 确认
```

**复用性**：M4 反问式学习也能调 orchestrator（"按这门课的薄弱点生成一套复习材料" → flashcards + mock_questions 多 tool 组合）。

### 新增 tasks

| Task | 触发例句 | 主要动作 |
|---|---|---|
| `task-orchestrator.md` | （内部调用，不直接面向用户） | 接收任务画像 → 编排 tool 调用 → 执行 |
| `do-homework.md` | "帮我完成 DSAA2043 hw3" | 识别 → 询问意图 → 调 orchestrator → 提交 |
| `write-notes.md` | "给 Deep Learning lecture 3 写笔记" | 下载 slides → 调 orchestrator（pdf-reader + writing-helper + pdf-renderer） |
| `weekly-plan.md` | "帮我规划下周学习" | 综合 ddl + 评分占比 + 难度估计 → 生成日程 |

### `do-homework.md` 软交互流程

不是每步都卡用户，**只两个询问点**：

```
用户："帮我完成 DSAA2043 hw3"
  ↓
[A] Agent 找题 → 读懂题面 → 识别类型
  ↓
[B] ★ 询问点 1：摘要 + 询问意图
       "DSAA2043 hw3：5 道动态规划证明题 + 2 道 OJ 编程题，ddl 12-13 15:59。
        要我直接做吗？"
       AskUserQuestion: [是 / 只做某几题 / 不用]
  ↓
[C] 用户同意 → 调 task-orchestrator
       orchestrator 内部完成 skill 调度 + 连贯执行
       中间只在遇到必须问的歧义时才中断
  ↓
[D] 完成后：草稿展示
  ↓
[E] ★ 询问点 2：提交确认
       AskUserQuestion: [API 自动提交 Canvas / 我先看 markdown / 取消]
  ↓
[F] 用户确认 → 调 Canvas POST /api/v1/.../submissions
```

### M3 第一个可演示子集：Report 流水线

M3 不可能一口气把所有产出能力做完。首发选 **Report** 类作业（最常见、价值高、风险低）：

**目标场景**：
- DLED3020 Paper Critique（学术批判性 essay）
- UCUG1809 Reflective Essay（反思性写作）

**首发内置 tools**：
| Tool | 能力 | 备注 |
|---|---|---|
| `tools/_index.md` | 维护可用 tool 清单 + 能力描述 | orchestrator 查这个 |
| `tools/paper-search.md` | 文献搜索（先用 arxiv API / Google Scholar 链接生成） | M3 阶段不做全文抓取 |
| `tools/figure-maker.md` | 数据可视化（matplotlib 代码生成 + 渲染） | 主要服务 report 中的图表 |
| `tools/writing-helper.md` | essay 结构化生成（intro / body / conclusion） | 含引用格式（APA / IEEE） |
| `tools/pdf-renderer.md` | Markdown → PDF（pandoc + xelatex，含中文字体 + callout.lua） | 抄 AutoPku 的踩坑经验 |

**端到端验收**：
- [ ] 用户说"帮我完成 DLED3020 Assessment Task 3 (Paper Critique)"
- [ ] agent 识别为 report 类，summary 给用户确认
- [ ] orchestrator 调度：paper-search 找参考文献 → writing-helper 起草 → pdf-renderer 出 PDF
- [ ] 用户审核后通过 Canvas API 提交（或本地保存）
- [ ] 全程只有 [B][E] 两个 AskUserQuestion

### 后续场景（M3 内逐步加）

完成 Report 后再加 tools 支持其他场景：

| 场景 | 新增 tool | 示例作业 |
|---|---|---|
| Presentation | `tools/slide-maker.md` (marp/reveal-md) | UCUG1077 group presentation |
| 理论题集 | `tools/proof-solver.md` + `tools/math-renderer.md` | DSAA2043 / DSAA3051 |
| 代码作业 (Canvas 内) | `tools/code-writer.md` | DSAA2012 project |
| 多模态视频 | `tools/video-maker.md` (ffmpeg + manim) | 未来选修课用得到 |

每加一个 tool，orchestrator 自动获得新能力 —— 因为它读的是 `tools/_index.md`，不写死类型。

### 第三方链接（OJ / 外部表单）处理原则

**默认路径（推荐）**：让学生把题目内容**存到本地**，agent 在本地完成解题，输出给学生手动复制粘贴。

**可选路径（需用户明确同意）**：playwright 模拟浏览器操作。但默认建议**不走** —— 涉及未知站点的认证、风控、合规风险。

写到 SKILL.md 的安全规则里。

### Canvas API 自动提交（M3 验证项）

需要验证 `POST /api/v1/courses/:id/assignments/:aid/submissions` 在 HKUST(GZ) 实例上可用 + 支持的 submission_type。

**安全规则**：
- 不自动选择最新作业（必须用户在 [B] 明确指定）
- 提交前必须 [E] 确认
- 失败时清晰提示，不重试

### 设计要点

- **不假设"全部代写"**：[B] 给用户"只做某几题"的选项，尊重学生想自己做部分的需求
- **产物沉淀本地**：每份草稿存到 `data/homework/<course>/<hw>/`，不是丢在 chat session
- **群组作业拒绝代做**：识别到 group 类型时主动告知"这类涉及组员协作，不适合 agent 全权代做"
- **Tool 之间用文件传递**：orchestrator 不把 tool 当函数调用，而是把中间产物落地到 `data/homework/.../intermediate/`，每个 tool 读写文件。这样：
  - tool 单独可测试
  - 失败可断点续跑
  - 用户可以中途接管某一步

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
- **提示梯度**：Socratic → hint → 部分解 → 完整解，agent 根据用户多次答错的程度递进
- **不给完整答案是默认行为**（写进 SKILL.md 的 safety section）

---

## M5. 多平台 + 主动提醒

**目标**：覆盖完整的 5 模块、打通跨 agent 平台、引入主动性。

### M5a 多 runtime 适配

参考 AutoPku 的 `sub-skills/runtime/`：
- `claude-team.md` — Agent Team 并行
- `codex-subagent.md` — Codex native subagents
- `kimi-team.md` — Kimi Code CLI

每门课的资源拉取并行化（6 个 agents 同时跑），从串行 30s → 并行 5s。

### M5b 主动提醒（Proactive Reminder）

这是 PDF 里强调的"区别普通 Web Chat 的关键"。技术路径：

- 用 Claude Code 的 **hooks** 机制配置 cron-like 触发
- 例如 `SessionStart` hook 检查 ddl，距离 < 48h 的高亮提醒
- 或用 `CronCreate` 工具创建定时任务（每天早上 9 点检查 ddl）

---

## 跨阶段的几个原则

### 1. 安全边界从 M2 开始就立起来

- 不回显登录态
- 下载、提交、外发任何操作前都用 `AskUserQuestion` 确认
- 不自动选择"最新"的作业 / 课件 / 公告

### 2. 踩坑回灌

每次实战发现的问题（PDF 渲染、cookie 过期、特殊字符路径）都写回对应的 sub-skill 文件 + PITFALLS.md，让下次执行的 agent 直接绕开。这是 AutoPku 第十一阶段的核心经验。

### 3. 单体先 → 模块化再

不要一开始就上三层架构。M2 就一个 `skill.md` + 一个 `sync-status.md` 即可。等到第二、第三个 task 出现明显重复时再抽 `tools/` 和 `runtime/`。

### 4. 端到端 > 完整

宁可一个 task 跑通端到端，也不要五个 task 各完成 80%。M2 验收标准里"一个陌生用户能跑通"比"功能多"重要。

---

## 不在 roadmap 里的事

明确**不做**的：

- ❌ 自建 Web UI / 桌面应用 — 完全寄生在 Claude Code / Codex 上
- ❌ 自建后端服务 / 数据库 — 数据全部本地文件
- ❌ 多用户协同 / 班级共享 — 单人本地工具
- ❌ Notion / Obsidian 双向同步 — 留给用户自己用文件系统接
- ❌ 自动注册账号 / 选课操作 — 风险太高、价值不高

---

## 当前位置

```
[M1 ✅] ──→ [M2 ✅] ──→ [M3 🎯] ──→ [M4] ──→ [M5]
                         ↑
                       准备进入
```

**M2 已落锁**（commit `7e6725e`），验证了 agent 看着 skill.md 能跑通 sync-status 任务。

**M3 下一步**：先实现 `task-orchestrator.md` + `tools/_index.md` 调度框架，配合 Report 流水线的 4 个内置 tool（paper-search / figure-maker / writing-helper / pdf-renderer），端到端跑通一个 DLED3020 paper critique。

**M3 推荐起步顺序**：
1. 写 `tools/_index.md` 框架（即使只有一个 tool）—— 让 orchestrator 有东西可读
2. 写 `tools/pdf-renderer.md` —— 最稳的纯工具，任何 task 都用
3. 写 `tasks/task-orchestrator.md` 骨架 —— 接收任务画像，简单版只调 pdf-renderer 就能演示
4. 写 `tasks/do-homework.md` —— 用 orchestrator 跑通一个真实作业
5. 补 writing-helper / paper-search / figure-maker，逐步覆盖 report 类完整流水线
