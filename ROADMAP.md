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

## M3. 学习材料 + 作业辅助

**目标**：从"看到信息"升级到"产出材料"。让用户能用自然语言指挥 agent 完成两类高频任务：写笔记、做作业。

### 新增 tasks

| Task | 触发例句 | 主要动作 |
|---|---|---|
| `write-notes.md` | "给 Deep Learning lecture 3 写笔记" | 下载 slides → PDF 解析 → 生成 markdown 笔记 → 渲染 PDF |
| `do-homework.md` | "帮我完成 DSAA2043 hw3" | 识别作业类型 → 软交互询问 → 完成 → API 提交 |
| `weekly-plan.md` | "帮我规划下周学习" | 综合 ddl + 评分占比 + 难度估计 → 生成日程 |

### `do-homework.md` 的软交互流程（关键设计）

不是每步都卡用户，而是**两个询问点 + 中间连贯执行**：

```
用户："帮我完成 DSAA2043 hw3"
  ↓
[A] Agent 找题 → 读懂题面 → 识别类型
       (essay / problem set / coding / presentation / group)
  ↓
[B] ★ 询问点 1：简短摘要 + 询问意图
       "DSAA2043 hw3：5 道动态规划证明题 + 2 道 OJ 编程题，ddl 12-13 15:59。
        要我直接做吗？"
       AskUserQuestion:
         [是，全部做 / 只做某几题 / 不用]
  ↓
[C] 用户同意 → agent 连贯完成（不再频繁打断）
       中间只在遇到必须问的歧义时才中断
  ↓
[D] 完成后：草稿展示 + 询问是否提交
  ↓
[E] ★ 询问点 2：提交确认
       AskUserQuestion: [API 自动提交 Canvas / 我先看 markdown / 取消]
  ↓
[F] 用户确认 → 调 Canvas POST /api/v1/courses/:id/assignments/:aid/submissions
```

**只有两个询问点**：[B] 开始前、[E] 提交前。中间执行不打断。

### 按作业类型分发

```
do-homework.md (主入口)
  ├─ 写作类  → tools/writing-helper.md
  ├─ 理论题集 → tools/proof-solver.md
  ├─ 编程题（Canvas 内）→ tools/code-writer.md（生成代码 → 渲染 → 提交）
  ├─ 编程题（OJ 等第三方）→ 见下条"第三方链接处理"
  ├─ Presentation → tools/slide-maker.md
  └─ Group project → 拒绝代做，只能辅助单人贡献部分
```

### 第三方链接（OJ / 外部表单）处理原则

**默认路径（推荐）**：让学生把题目内容**存到本地**，agent 在本地完成解题，输出给学生手动复制粘贴到第三方站点。

**可选路径（需用户明确同意）**：playwright 模拟浏览器操作第三方站点。但默认建议**不走这条路** —— 涉及未知站点的认证、风控、合规风险。skill 提示用户时要明确标注"不推荐"。

写到 SKILL.md 的安全规则里：
> 涉及第三方站点（OJ、外部表单）时，默认建议学生把题目保存到本地由 agent 辅助。
> 自动化第三方操作必须 AskUserQuestion 明确告知风险后才能进行。

### Canvas API 自动提交（M3 验证项）

需要验证 `POST /api/v1/courses/:id/assignments/:aid/submissions` 在 HKUST(GZ) 实例上可用 + 支持的 submission_type（online_upload / online_text_entry / online_url）。

**安全规则**：
- 不自动选择最新作业（必须用户在 [B] 明确指定）
- 提交前必须 [E] 确认
- 失败时清晰提示，不重试

### 新增 tools

- `tools/pdf-renderer.md` — Markdown → PDF（学 AutoPku 的 pandoc + xelatex + callout.lua）
- `tools/writing-helper.md` — essay / reflection / annotated bib 的结构化生成
- `tools/proof-solver.md` — 数学证明、复杂度分析的解题模板
- `tools/code-writer.md` — 代码生成 + 单元测试 + 注释
- `tools/slide-maker.md` — Markdown → marp/reveal.js → PDF/PPTX

### 设计要点

- **不自动假设"全部代写"**：[B] 给用户"只做某几题"的选项，尊重学生想自己做部分的需求
- **生成内容沉淀到本地**：每份草稿存到 `data/homework/<course>/<hw>/`，不是丢在 chat session 里
- **群组作业拒绝代做**：识别到 group 类型时主动告知"这类作业涉及组员协作，不适合 agent 全权代做"

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
[M1 ✅] ──→ [M2 🎯] ──→ [M3] ──→ [M4] ──→ [M5]
              ↑
            你在这里
```

**下一步**：决定 M2 的具体范围 —— 是先做"同步状态"一个 task 跑通端到端，还是先把目录结构搭起来再填内容？

我推荐前者：**先做窄而完整的切片，让 skill 真的能被 load 起来用，再扩展。**
