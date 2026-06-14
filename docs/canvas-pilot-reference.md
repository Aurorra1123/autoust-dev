# Canvas Pilot 项目设计发现与 AutoStudy 开发建议

> 基于 canvas_copilot（下称 Canvas Pilot）项目的深度调查，提炼出对 AutoStudy 有参考价值的设计思想。
> Canvas Pilot 是一个面向通用 Canvas 学校的作业自动化框架，定位与 AutoStudy 不同（通用 turnkey 产品 vs 本地 Canvas LMS assistant skill，当前已在 HKUST(GZ) 验证），但在工程设计和架构思路上有不少值得借鉴的地方。
> 本文不建议照搬其架构，而是提炼思想、结合 AutoStudy 的 5 模块愿景和现有 ROADMAP 讨论后续开发方向。

---

## 1. 最值得参考的四个设计思想

### 1.1 深度 Spec 侦查

#### Canvas Pilot 的做法

Canvas Pilot 有一个叫 **canvas-generic** 的核心编排器。它的设计思路是：遇到任何作业，不急于动手，而是先做一轮完整的"侦查"，搞清楚到底要做什么，再决定怎么做。

具体来说，当前最值得 AutoStudy 学的不是某个脚本，而是
`canvas-generic` 的阶段边界：

**第一步：从 Canvas 拉取所有可能相关的信息源。** 不只看作业页面的 description 和附件，还会：

- 读取课程的 **Front Page**（很多教授把作业要求写在课程首页）
- 遍历课程的 **Modules**（很多课程按周组织，作业 spec 散落在某个 module item 里）
- 获取 **Syllabus**（课程大纲，常包含评分标准和作业格式要求）
- 抓取 **外部链接**（有些作业 spec 链到教授个人网站或 GitHub）
- 下载所有 **附件**

这一步的产出是一个标准化 `spec.md` 报告。它不是 raw dump，而是 agent
看完来源后写出的判断：哪些来源检查过、哪个是主 spec、交付物是什么、
证据文件在哪里、还有什么缺口。完整 PDF / Google Doc / 网页正文放在
`references/`。

**第二步：搜索评分标准（Rubric）。** 不只在 Canvas API 提供的 rubric 字段里找，还会在 `spec.md`、PDF、module/syllabus、外部链接里找。四层搜索确保不遗漏，结果写入 `investigation/rubric.md`。

**第三步：定位真正需要的输入。** 下载或抓取 PDF、Google Doc、starter code、数据集、外部文本等，放到 `references/`。无法访问的资源写入 `investigation/unreachable.txt`。

**第四步：完整性审查。** 侦查完成后，优先用另一个 reviewer / sub-agent 审查"我们搞清楚了到底要做什么吗？"——交付物明确吗？rubric 找到了吗？input 文件齐了吗？不可达资源是否阻塞？如果当前运行环境没有 sub-agent reviewer，就必须冷读 `spec.md`、`rubric.md`、`references/`、`unreachable.txt` 重新审一遍，并在 `investigation/review_a.json` 里记录审查方式。

**第五步：分类交付物形态。** 根据 `spec.md`、rubric、submission types 和 `references/` 判断输出模式：`doc_prose`、`pdf_annotated`、`pdf_typed`、`code`、`form_answers`、`slides`、`mixed`。这个判断成为 `pipeline_design.md` 的第一行。

#### 对 AutoStudy 的启发

AutoStudy MVP 时的 `assignment-recon` 主要看 `assignment.json.description`
里的附件链接，然后下载附件、提取文本。对于"作业要求都写在附件里"的
场景，这能跑通 demo，但不够稳定。

但从 AutoStudy.pdf 模块 1（Course Context Manager）和模块 5（Assignment & Academic Production）的愿景来看，我们需要的是更完整的课程材料获取能力。很多课程的作业 spec 不在附件里，而是在 Modules、Syllabus、课程首页、甚至外部链接中。特别是 HKUST(GZ) 的课程，教授们的组织习惯差异很大——有的把所有东西放在 assignment description 里，有的把 spec 写在 module page 里，有的链到自己的 Google Site。

#### 需要做什么

这涉及 **canvascli 的扩展**，因为 AutoStudy 的架构是 canvascli 独立仓库提供数据层，skill 层通过 shell out 调用。数据层扩展已经完成，下一步重点在 AutoStudy 的 agent-led 侦查和 pipeline 执行。

**canvascli 侧**（Copilot 式原子命令）：

- `canvascli assignment <aid> --course-id <cid>` — 作业页面、description、submission/rubric metadata、HTML 中的文件和外链提示
- `canvascli rubric <aid> --course-id <cid>` — Canvas rubric / rubric assessment
- `canvascli front-page --course-id <cid>` — 课程首页
- `canvascli syllabus --course-id <cid>` — 课程大纲
- `canvascli modules --course-id <cid>` — module 列表
- `canvascli module-items <module-id> --course-id <cid>` — 单个 module 的 items
- `canvascli page <page-url> --course-id <cid>` — Canvas wiki page 正文
- `canvascli file <file-id>` — 文件元数据
- `canvascli assignment-files <aid> --course-id <cid>` — assignment 直接附件和 description 直链文件

这里明确不采用 `assignment-context` / `full-context` 聚合命令。Canvas Copilot 的成熟经验是：数据层提供稳定的单源读取能力，上层 agent 必须逐源查看，再判断哪个来源才是真正的 spec。聚合命令看似方便，但容易把"是否相关"这个判断提前固化到数据层，降低灵活性。

**AutoStudy skill 侧**（当前批准方向）：

- `assignment-recon.md` 正式采用 agent-led Canvas Generic Stage 1-5。
- 不保留脚本化 spec 生成路径；原子 CLI 只提供来源读取能力，主 spec 判断、`spec.md`、`review_a.json` 和 output mode 必须由 agent 逐源阅读后写入。
- `spec.md` 是标准化侦查报告，不是 source dump。
- `problem.md` 只是旧工具兼容层，长期会继续缩薄。
- `do-homework [B]` 必须向用户汇报侦查结果并运行 alignment loop，即使 `review_a.json.verdict == "proceed"`。简单作业少问几轮，开放性作业持续追问，直到 Main Agent 能不靠脑补开始执行。
- `do-homework [B]` 的多轮过程写入 `investigation/user_notes.md`；只有当 Main Agent 判断没有必须继续问的问题时，才写 `investigation/alignment_brief.md` 并请求用户确认。
- `do-homework [C]` 在确认后的 `alignment_brief.md` 基础上完成 `pipeline_design.md`，然后 `task-orchestrator` 按这个文件执行。

#### 真实例子：DSAA2011 和 UCUG1505

这两个真实 case 解释了为什么必须逐源侦查，而不是只读 assignment description。

**DSAA2011 Project**：

- assignment description 为空
- Canvas rubric 没有
- front page 404 / 未启用
- syllabus 有课程级内容但不是项目 spec
- modules 有 4 个，真正项目说明在 module item 文件里
- `DSAA2011-26sp-project_announce-L01.pdf` 是主 spec，其他 review / sample PDF 是上下文

如果 AutoStudy 只读 `assignment.description`，这里会得到"空作业"。Copilot 式流程会继续看 modules 和 module items，所以能找到项目说明 PDF。

**UCUG1505 FINAL project**：

- assignment description 里直接有 Google Doc spec 外链
- Week 4 module item 也有同一个 "Final project specification"
- Week 9 slides 是邻近上下文
- rubric / assignment files 都没有

这里的正确判断不是"第一个链接就是全部"，而是看完 assignment + module items 后发现 Google Doc 是主 spec，slides 是补充材料。

---

### 1.1.1 单作业工作台结构

#### Canvas Pilot 的真实 run 结构

2026-06-01 的 DSAA2011 Project run 目录展示了 Canvas Pilot 最值得学习的结构：

```text
runs/2026-06-01/DSAA2011_L01_-_Machine_Learning__Project/
├── spec.md
├── references/
│   ├── DSAA2011-26sp-project_announce-L01.pdf
│   ├── DSAA2011-exam_sample.pdf
│   └── DSAA2011-Final_review.pdf
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
├── pipeline_design.md
├── draft/
│   ├── project_group01_dropout.ipynb
│   └── requirements_group01_dropout.txt
├── verification_checklist.md
├── verification.log
└── result.json
```

这个目录的核心不是"文件名好看"，而是每个文件对应一个阶段和责任：

- `spec.md`：完整作业上下文，不信任单一 Canvas description
- `references/`：下载到本地的 PDF、starter code、数据、网页文本等可引用材料
- `investigation/`：rubric、不可达资源、侦查完整性审查
- `pipeline_design.md`：根据 spec 和 rubric 现场设计的产出方式
- `draft/`：实际草稿和交付物源文件
- `verification_checklist.md` / `verification.log`：可机械检查的验收标准与结果
- `result.json`：这个 assignment 的流程状态收据，供跨 session 恢复和上层调度读取；它不替代 `spec.md` / `review_a.json` 的侦查记录

#### AutoStudy 应采用的过渡结构

当前 AutoStudy 的 `data/homework/<COURSE>/<HWID>/` 更像一个平铺材料夹。MVP 可用，但 mixed task 会很快变乱。下一步应该向 Canvas Pilot 的单作业工作台靠拢：

```text
data/homework/<COURSE>/<HWID>/
├── canvas/
│   ├── assignment.json
│   ├── rubric.json
│   ├── front-page.json
│   ├── syllabus.json
│   ├── modules.json
│   └── module-items-<mid>.json
├── spec.md
├── problem.md
├── references/
├── investigation/
│   ├── rubric.md
│   ├── unreachable.txt
│   └── review_a.json
├── pipeline_design.md
├── draft/
├── verification_checklist.md
├── verification.log
└── result.json
```

`canvas/` 保存原子 CLI 返回结果，作为取数证据。`spec.md` 成为侦查后的主文件。`problem.md` 暂时保留为兼容层，因为现有 tools 仍读取它。`draft/` 承载多产物，适合 notebook + report + slides + zip 这种混合任务。`result.json` 是 do-homework 流程的状态收据：用户跳过、草稿完成、验证失败、提交成功时写；单纯侦查完成只写 `spec.md` 和 `investigation/review_a.json`。

---

### 1.2 侦查后的动态管线组合

#### 侦查之后，Canvas Pilot 做了什么

上节讲了 canvas-generic 怎么做侦查。侦查只是第一步，更关键的差异在侦查之后：**它不是查一张固定流水线表来决定怎么做，而是根据侦查结果动态组合执行步骤。**

具体来说，canvas-generic 在侦查完成后会做两件事：

**第一步：分类交付物形态。** 根据侦查到的 spec 内容，判断这个作业要产出的东西属于哪一类——是纯文本文档（doc_prose）、需要手写填空的 PDF（pdf_annotated）、需要打字回答的 PDF（pdf_typed）、代码项目（code）、表单问答（form_answers）、还是混合型（mixed，同时包含多种形态）。

**第二步：按形态动态生成执行步骤。** 不是从一个固定映射表里选 pipeline，而是根据分类结果和 rubric 要求，实时生成"先做什么、再做什么"的步骤列表。比如一个 mixed 类型的作业被分解为多个子 pipeline 独立执行，最后合并产出。

这个过程没有硬编码的 `if type == "paper": [search, write, render]`。每一步都是根据实际需要动态决定的。

#### AutoStudy 的迁移方式

MVP 阶段 `task-orchestrator.md` 的编排是**固定流水线**模式：

```
paper  → search_papers → make_figure → write_essay → render_pdf
slides → make_figure → render_slides
math   → write_essay → render_pdf
lab    → write_code → run_tests → write_essay → render_pdf
```

路由靠关键词启发式：`problem.md` 里出现 "essay" -> paper，出现 "prove" -> math，出现 "implement" -> lab。然后查 `_index.md` 的 Scenario -> Tool chain 表，走固定链。

这种模式在 MVP 阶段验证的 4 个场景（paper/slides/math/lab）里工作得很好，因为每个场景确实只有一种明确的交付物类型。但它有两个结构性弱点：

1. **复杂/混合任务无法处理。** 如果一个作业同时要求"搜集文献 + 写代码实验 + 撰写 report + 做 presentation"，当前的设计只能选择权重最高的一个类型（`mixed` 类型的处理方式是"pick the highest-weight one"），或者回退给用户。这意味着一个本可以自动化的复杂任务被简化了或放弃了。

2. **扩展新类型需要改表。** 每增加一种作业类型，都需要在 `_index.md` 加一条固定链、在 `task-orchestrator.md` 的启发式表里加一行映射。这是一种"枚举所有可能"的思路，随着类型增多会越来越难维护。

#### 当前批准方向：`pipeline_design.md` 是执行契约

我们不再让 orchestrator 从 `task_profile.yaml` 或固定 `required_capabilities`
列表启动。当前方向是：

```text
spec.md + rubric.md + references/ + confirmed alignment_brief.md
  -> do-homework [C] writes pipeline_design.md
  -> task-orchestrator executes pipeline_design.md
  -> tools read the workbench and write draft/ + verification artifacts
```

也就是说，动态组合不是"临时 fallback"，而是通过 `pipeline_design.md` 变成
单作业执行计划。`_index.md` 仍然是工具注册表，但它提供的是可用 tool 和
能力说明，不再是固定路由表。

具体来说：

**保持现有 tools 不变**——paper-search、figure-maker、writing-helper、
pdf-renderer、code-writer、test-runner、slide-maker 各自仍然是独立的 skill
文件，各自定义清楚输入输出。

**改变 orchestrator 的编排方式**——从"查固定链"变成"执行
`pipeline_design.md`"：

- 一个"搜集文献 + 代码实验 + report + slides"的作业，`pipeline_design.md`
  会写成多个 sub-pipeline：code、report、slides、package。
- 一个纯 math proof 作业，`pipeline_design.md` 可能只包含 typed-PDF prose
  stage 和 render stage。
- 一个只有代码的 lab，`pipeline_design.md` 可能只包含 code-writer 和
  test-runner。

这种方式的鲁棒性更强，因为：

- **不依赖关键词匹配到固定类型的映射**。即使作业类型没有被预定义过，orchestrator 仍然可以分析出"这个任务需要哪些能力"并调用对应的 tools。
- **自然支持混合任务**。不需要 special-case 处理 mixed 类型——每个子任务各自调用对应的 skill，组合在一起就是完整的 pipeline。
- **新增 tool 不需要改 orchestrator 的路由表**。只要新 tool 在 `_index.md` 注册了能力和输入输出，orchestrator 就能根据任务需要自动引入。

**可以配合 course-overrides 做课程级指引。** 不同的课程可能有不同的"常用技能组合"——比如某门课的作业几乎总是涉及"读 paper + 写 critique"，那可以在 `course-overrides.yaml` 里记录这个偏好，让 orchestrator 在分析时参考。这比为每门课写专用 pipeline 轻量得多。

#### 与现有架构的关系

这个改动仍然是渐进式的：

1. M3 已验证的 tools 继续保留。
2. `problem.md` 暂时保留，避免旧工具立刻断掉。
3. 新的正式 flow 以 `spec.md -> alignment_brief.md -> pipeline_design.md -> draft/` 为准。
4. 需要在 DSAA2011 Project 和 UCUG1505 FINAL project 上做真实 flow
   连通测试，确认新文档指导下能产生和 Canvas Copilot 同等清晰的计划。

---

### 1.3 结构化状态管理

#### Canvas Pilot 的做法

Canvas Pilot 用几个 JSON 文件来记录运行状态，让 agent 能跨 session 恢复、避免重复工作。核心是三个文件：

- **`plan.json`** — 记录当前计划要做什么。scan 阶段生成后停下，等用户审批。包含每个作业的 ID、名称、优先级、用户是否批准。
- **`result.json`** — 每个作业完成后写一个，记录结果状态：`draft_ready`（草稿完成）/ `submitted`（已提交）/ `skipped`（跳过）/ `error`（出错）。
- **`_processed.json`** — 跨天的"已处理"账本。记录哪些作业已经做过了，下次 scan 时自动跳过。

这套机制解决的核心问题是：**agent 关掉再打开后，能知道之前做过什么、没做什么，不需要从头来。**

#### 对 AutoStudy 的启发

当前 AutoStudy 没有结构化的运行状态：

- `sync-status` 每次都是全量同步，没有"已处理"概念
- `do-homework` 的中间产物（`spec.md`、`pipeline_design.md`、各种 draft）存在 `data/homework/` 下，但没有一个统一的"这个作业做到哪了"的状态记录
- 跨 session 恢复靠 `agent-progress.md` 的自然语言交接日志，agent 需要读完整个文件才能推断状态

这不止影响 do-homework，更影响 AutoStudy.pdf 里的模块 2（Proactive Task Reminder）。要实现"DDL 提醒、优先级排序、进度追踪"，前提是有结构化的状态记录——否则 agent 无法判断"哪些作业已经做了、哪些还没开始、哪些快到期了"。

#### 建议怎么做

不需要像 Canvas Pilot 那么重（它还有 `_processed.json` 跨天 ledger、`plan.json` 审批门控等），但一个轻量的 `result.json` 就能解决大部分问题。注意：`result.json` 不在单纯侦查结束时写；侦查阶段的判断放在 `investigation/review_a.json`，而 `result.json` 由 do-homework 在用户确认后续动作或流程结束时写：

```json
{
  "course": "DSAA2043",
  "assignment_id": "12345",
  "status": "draft_ready",
  "spec_md": "data/homework/DSAA2043/12345/spec.md",
  "problem_md": "data/homework/DSAA2043/12345/problem.md",
  "deliverables": ["data/homework/DSAA2043/12345/solution.pdf"],
  "verification_log_path": "data/homework/DSAA2043/12345/verification.log",
  "human_review_items": [],
  "updated_at": "2026-06-01T14:30:00Z"
}
```

放在 `data/homework/<COURSE>/<HWID>/result.json`，do-homework 写，sync-status 后续可读。这样 sync-status 就能展示"这门课有 3 个作业已完成草稿、2 个未开始"，而不是只展示 DDL。`status: draft_ready` 的含义是草稿/初版交付物已经生成但尚未提交；`status: skipped` 可表示用户在侦查汇报后选择暂不继续。

对于模块 2（Proactive Task Reminder），这个 `result.json` 加上 Canvas 的 submission 状态就是优先级排序的基础。

AutoStudy 采用一个稳定脚本写这个状态文件，避免 agent 每次手写 JSON：

```bash
.venv/bin/python scripts/write_homework_result.py \
  --work-dir "data/homework/DSAA2043/hw3" \
  --status draft_ready \
  --deliverable "data/homework/DSAA2043/hw3/draft/final.pdf" \
  --verification-log "data/homework/DSAA2043/hw3/verification.log"
```

四个状态的含义：

- `skipped`：用户在侦查汇报后选择先不做，或未来 plan 执行时明确 defer。
- `draft_ready`：草稿/初版交付物已经生成，但未提交 Canvas。
- `submitted`：用户确认后已经提交 Canvas。
- `error`：侦查后续、生成、验证或提交流程失败，需要用户或开发者处理。

#### `data/runs/<today>` 和 `data/homework/<COURSE>/<HWID>` 的关系

Canvas Pilot 有 scan/execute 两层：`runs/<today>/plan.json` 是今天这批
作业的执行计划，`runs/<today>/<assignment>/result.json` 是单个作业的结果。

AutoStudy 后续可以借鉴这层，但命名要更符合助手型产品。建议用：

```text
data/runs/<today>/
├── raw/
│   ├── courses.json
│   ├── assignments.json
│   └── announcements.json
├── pending_assignments.json
├── plan.json
└── REPORT.md

data/homework/<COURSE>/<HWID>/
├── spec.md
├── draft/
└── result.json
```

两者不冲突：`data/runs/<today>/pending_assignments.json` 记录"今天扫到哪些
作业、用户想处理哪些"，只保存轻量索引和 `work_dir` 指针；`data/homework`
保存具体作业的侦查、材料、草稿、验证和结果。也就是说：

```text
daily plan item -> points to -> assignment workbench
```

注意这里的 `pending_assignments.json` 不等于
`data/homework/<COURSE>/<HWID>/canvas/assignment.json`。前者是一批作业的扫描
列表；后者是某个 Canvas assignment 的原始 API 快照。

#### AutoStudy 的 scan-plan 适配

Canvas Pilot 的成熟边界是：`canvas-scan` 只扫描、分桶、写 `plan.json`，
然后停止；`canvas-execute` 读用户批准后的计划再执行。这个边界值得直接
学习，因为它把"提出建议"和"采取行动"分开，防止 agent 在用户还没批准时
启动一串作业流程。

AutoStudy 采用同一个边界，但换成交互更轻的助手形态：

```text
sync-status
  -> canvascli courses / assignments / announcements
  -> scripts/write_scan_plan.py
  -> data/runs/<today>/pending_assignments.json
  -> data/runs/<today>/plan.json
  -> data/runs/<today>/REPORT.md
  -> AskUserQuestion: choose one item, review a draft, or stop

do-homework
  -> only starts after the user chooses one item
  -> single-assignment workbench under data/homework/<COURSE>/<HWID>/
```

The stable writer is:

```bash
.venv/bin/python scripts/write_scan_plan.py
```

It reads `data/sync/current/assignments.json`, `data/sync/current/courses.json`, and
`data/homework/**/result.json`. It does not call Canvas and does not execute
homework. Its job is to combine current Canvas facts with local workflow state:

- Canvas `submitted` / `graded` items are filtered out by default.
- local `result.json.status == draft_ready` changes the suggested action to
  `review_or_submit`.
- local `result.json.status == skipped` or `submitted` keeps the item out of the
  plan unless explicitly deferred.
- unsubmitted project/report/lab/homework-like items are suggested as `recon`.

This gives AutoStudy the useful part of Canvas Pilot's state discipline without
turning `sync-status` into a batch executor. The user still chooses what happens
next.

The stable handoff from a numbered plan item to a single-assignment workflow is:

```bash
.venv/bin/python scripts/select_plan_item.py --index <N>
```

It reads today's `plan.json` plus `pending_assignments.json` and returns the
selected `course_id`, `assignment_id`, `assignment_name`, `recommended_action`,
and `suggested_work_dir`. This keeps the assistant from re-matching assignment
titles after the user has already chosen an item from the plan.

---

### 1.4 关键路径的轻量 Hook

#### Canvas Pilot 的做法

Canvas Pilot 在 Claude Code 的 `settings.json` 里配置了 **hooks**——在 agent 执行特定操作前/后自动触发的检查脚本。

举几个具体的例子：

- **提交前审计 hook**：当 agent 要执行 `canvascli submit` 或类似提交操作时，hook 先检查是否已经跑了验证清单。如果没有验证记录，直接阻止提交，返回错误信息。
- **result schema 验证 hook**：当 agent 写 `result.json` 时，hook 检查文件格式是否合规（status 字段是不是合法值、必填字段是否齐全），不合规就阻止。
- **泄漏检测 hook**：当 agent 执行 `git add` / `git commit` / `git push` 时，hook 扫描 diff 中是否包含学校名、课程 ID、邮箱等敏感信息模式，有则阻止。
- **完成性检查 hook**：当 agent session 要结束时，hook 检查是否所有分配到的任务都产出了 `result.json`，有遗漏就阻止退出。

这些 hook 的共同点是：**把安全规则从 prose 描述变成代码强制执行**。agent 无法绕过，因为它不是"被告知不要做"，而是"物理上做不到"。

#### 对 AutoStudy 的启发

当前 AutoStudy 的 `skill.md` 和 `do-homework.md` 里有大量的 Safety rules（8 条 + 7 条），但全部是 prose 描述，依赖 agent 的理解力和纪律。比如"不要自动提交，必须经过用户确认"——这是一个 prose 规则，agent 可以忽略。

这不是说当前不安全——MVP 阶段 agent 基本遵循了 safety rules。但随着 AutoStudy 功能扩展（模块 2 的定时提醒、模块 3 的材料生成），agent 需要做的事情越来越多，prose 规则的可靠性会下降。

#### 建议加哪几个 hook

不需要像 Canvas Pilot 那样 10 个 hook，但 **2-3 个关键 hook** 就能大幅提升可靠性：

1. **提交前审计**（PreToolUse）— 检查是否有用户确认记录，防止 agent 跳过 [E] 直接提交。这是 `do-homework.md` Safety #1 的代码强制版。
2. **result.json schema 验证**（PostToolUse）— 如果采用了 1.2 的建议加了 result.json，这个 hook 确保 agent 写的状态文件格式正确。
3. **敏感信息泄漏检测**（PreToolUse on git operations）— 当前被跟踪的文档中有真实的课程 ID（如 `2151`、`475078`）和学校域名，如果未来开源或公开，需要自动拦截新增的敏感信息。这个 hook 可以在 `git add` / `git commit` 时扫描。

Hook 的实现很简单：在 `.claude/settings.json` 的 `hooks` 字段下配置，每个 hook 就是一个 Python 脚本，exit 0 放行，exit 1 或 2 阻止并返回错误信息。具体格式参考 Claude Code 文档的 hooks 部分。

---

## 2. 当前 AutoStudy 开发路线

这份参考现在服务于 M3.5：把 MVP 的"能产出"升级成"能稳定理解作业，再按作业现场设计执行计划"。

### 已采用

| 事项 | 状态 | 说明 |
|------|------|------|
| canvascli 原子上下文命令 | 已完成 | `assignment` / `rubric` / `front-page` / `syllabus` / `modules` / `module-items` / `page` / `file` / `assignment-files` 已成为 CLI contract；不使用 `assignment-context`。 |
| 单作业 workbench | 已验证基础结构 | `data/homework/<COURSE>/<HWID>/` 使用 `canvas/`、`spec.md`、`references/`、`investigation/`、`pipeline_design.md`、`draft/`、`verification_*`、`result.json`；DSAA2011 / UCUG1505 已用本结构做真实验证。 |
| scan-plan 边界 | 已完成 | `sync-status` 只扫描并生成 `pending_assignments.json` / `plan.json` / `REPORT.md`，用户选择单项后才进入 `do-homework`。 |
| result.json | 已完成 | `do-homework` 写单作业状态收据；`review_a.json` 仍是侦查充分性的审查文件。 |
| agent-led Canvas Generic reconnaissance | 已验证 | 正式路径是 Stage 1-5 逐源侦查，不走脚本生成 spec；DSAA2011 / UCUG1505 已跑通到 `pipeline_design.md` 与 orchestrator dry-run。 |

### 已完成验证

| 事项 | 验证目标 | 说明 |
|------|------|------|
| DSAA2011 Project 真实 flow | 已通过 | 按原子来源完整读取，确认 assignment 页面为空、module PDF 是主 spec，写出 mixed `pipeline_design.md`：notebook/code、report PDF、presentation PDF、requirements、package；dry-run 正确停在 group/dataset/style-file human blockers。 |
| UCUG1505 FINAL project 真实 flow | 已通过 | 确认 assignment page 与 Week 4 module 指向同一个 Google Doc spec，Week 9 slides 是 supporting context，写出 mixed `pipeline_design.md`：code/source zip、documentation、video demo human item；dry-run 正确停在 partner/concept/code/video blockers。 |
| task-orchestrator 连通 | 已通过 dry-run | 用 `pipeline_design.md` 执行入口检查，而不是从 `task_profile.yaml` 或固定 scenario chain 启动；当前验证没有生成草稿，因为两例都需要用户补充。 |
| 工具逐步迁移 | 持续 | writing-helper / code-writer / slide-maker 已改为读 `spec.md + alignment_brief.md + pipeline_design.md`；后续实际 flow 中继续压缩 `problem.md` 的作用。 |
| M3-SUBMIT 真实作业 E2E | 待 sandbox | 仍需要一个真实未过期低风险作业验证 Canvas 三步 submit。 |

### 之后再考虑

| 事项 | 说明 |
|------|------|
| 轻量 hooks | 提交前审计、result schema 验证、敏感信息泄漏检测。 |
| course-overrides.yaml | 记录课程习惯，比如 spec 常见位置、常用交付格式、偏好的 pipeline 形状。 |
| _processed.json | 先不急；等 scan-plan + result.json + do-homework 真实 flow 稳定后，再判断是否需要跨天账本。 |
| 轻量 cron 自动化 | 对应主动提醒模块，但应在单作业 flow 稳定后再做。 |

---

## 3. 不建议参考的部分

以下内容虽然在 Canvas Pilot 中有设计或实现，但不适合 AutoStudy 的定位和场景：

| 内容 | 不参考的理由 |
|------|------------|
| **ZyBooks 集成** | 美国体系特有的在线学习平台，HKUST(GZ) 不使用 |
| **Quiz 自动提交（4-agent 仲裁）** | 伦理风险高，且 HKUST(GZ) 不一定使用 Classic Quizzes |
| **Humanizer（降低 AI 检测信号）** | 涉及学术诚信敏感地带，与 AutoStudy "agent 负责脏活，你负责审核" 的定位矛盾 |
| **Process_humanize（伪造 git 历史）** | 学术诚信红线 |
| **Codex sidecar 双驱动** | 增加一倍维护成本，AutoStudy 的 markdown skill 模式已经够用 |
| **完整的 10 个 hooks 体系** | 过度工程，2-3 个关键 hook 即可 |
| **_private / public 双仓库隔离** | AutoStudy 定位单校个人用，不需要产品级的公私隔离 |
| **批量自动 execute 默认行为** | AutoStudy 借鉴 scan/execute 的边界，但不照搬批处理执行体验。sync-status 只建议，do-homework 只在用户选择单项后执行。 |

---

## 4. 参考：Canvas Pilot 最值得直接阅读的文件

如果对上述设计思想感兴趣，以下是 Canvas Pilot 中最值得直接去读的几个文件（按优先级排列）：

| 文件 | 内容 | 为什么值得读 |
|------|------|------------|
| `.claude/skills/canvas-generic/SKILL.md` | canvas-generic 的完整 11-stage pipeline 设计 | 理解"先侦查再动手"和"侦查后动态管线组合"的完整思路。440 行，读一遍大概 15 分钟。重点关注 Stage 5（classify-output）和 Stage 6（design-pipeline）的动态组合逻辑。 |
| `docs/RUN_STATE_SCHEMA.md` | 状态文件 schema 定义 | 理解 plan.json / result.json / _processed.json 的具体格式设计。 |
| `.claude/settings.json` | hooks 配置 | 看看 hooks 是怎么在 settings.json 里声明的，具体格式是什么。 |
| `.claude/hooks/check-presubmit-audit.py` | 提交前审计 hook 实现 | 最实用的 hook 之一，看看 Python 脚本怎么检查、怎么阻止。 |
| `src/canvas_client.py` | Canvas API 客户端实现 | 理解它的 REST API 覆盖范围（16 读 + 8 写），对比 canvascli 当前的覆盖面。 |

---

## 5. 总结

AutoStudy 当前的 MVP（M3）已经验证了核心作业辅助能力。从 Canvas Pilot 的调查中，最值得吸收的不是代码或架构，而是四个设计思想：

1. **深度侦查再动手** — 不只看附件，从 Canvas 的多个信息源完整获取作业 spec；`spec.md` 是标准化判断报告，不是 raw dump。
2. **用 `pipeline_design.md` 现场设计执行** — 不从 `task_profile.yaml` 或固定 scenario chain 启动，而是让 do-homework 在用户确认 `alignment_brief.md` 后写出单作业计划，orchestrator 执行它。
3. **结构化状态记录** — 用 `result.json` 记录每个作业的状态，让 agent 跨 session 恢复，支撑模块 2 的进度追踪。
4. **关键路径代码强制** — 用 2-3 个 hooks 把最重要的安全规则从 prose 变成代码强制执行。

这些改动都是增量式的，不需要推翻现有 tools。当前第一步已经完成：DSAA2011 和 UCUG1505 两个真实任务跑通到 `spec.md -> pipeline_design.md -> task-orchestrator dry-run`。下一步不是重写侦查，而是在真实 clear/open 作业上验证 `alignment_brief.md` 对齐循环、human blockers、草稿执行与 revision loop。

---

## 6. Copilot canvas-generic 完整 11 阶段与 AutoStudy 对比

Canvas Copilot 的 `canvas-generic` 共有 **11 个 Stage（0-11）**，包含 3 个 sub-agent 审查和 1 个验证重试循环。AutoStudy 当前已完成前 5 个 Stage 的验证，后续 Stage 作为开发方向逐步对齐。

| Stage | 名称 | Copilot 做法 | AutoStudy 状态 | 差异说明 |
|---|---|---|---|---|
| 0 | load per-cluster learnings overlay | 读 `_private/canvas-generic-<course>-<cluster>.md`，加载累积用户偏好 | ❌ 未做 | AutoStudy 规划三层偏好体系：任务级 → 课程级 → 用户级（见 ROADMAP） |
| 1 | fetch-context | 拉所有来源 → 写 `spec.md` | ✅ 已验证 | AutoStudy 用 `canvascli` 原子命令实现，agent-led |
| 2 | find-rubric | 4 层搜索 → `investigation/rubric.md` | ✅ 已验证 |  |
| 3 | locate-inputs | 下载文件 → `references/` + `unreachable.txt` | ✅ 已验证 |  |
| 4 | Sub-agent A: review investigation | 完整性审查 → `review_a.json` | ⚠️ 已做但仅 cold self-review | 后续升级为独立 sub-agent |
| 5 | classify-output | 判断输出模式 → 写 `pipeline_design.md` 第一行 | ✅ 已验证 | AutoStudy 后续将输出模式 skills 化 |
| **6** | **design-pipeline** | 根据输出模式设计管线阶段 | ⚠️ 在 do-homework [C] 完成 | AutoStudy 的管线设计强调动态 skills 组合，不绑固定 pipeline |
| **7** | **generate** | 执行管线，产出 `draft/` | ❌ 待开发 | AutoStudy 强调多轮迭代：单次做不好可以继续打磨 |
| **8** | **Sub-agent B: design verification checklist** | 从 rubric 设计可量化验证清单 | ❌ 待开发 | 后续加入 |
| **9** | **verify + retry loop** | 运行验证，失败则重回 Stage 7（最多 3 次） | ❌ 待开发 | AutoStudy 的迭代不限于 3 次，支持跨轮次持续优化 |
| **10** | **Sub-agent C: review verification** | 审查验证覆盖度，防 false-pass | ❌ 待开发 | 后续加入 |
| **11** | **export + result.json** | 最终化草稿文件名，写 `result.json` | ⚠️ 部分实现 | AutoStudy 的 `result.json` 需支持 `revision_needed` 状态 |

### 关键架构差异

| 维度 | Canvas Copilot | AutoStudy |
|---|---|---|
| **产品形态** | 自动化批处理：scan → plan → approval → batch execute → report | 助手式交互：用户说一句话 → agent 侦查 → 汇报确认 → 执行 → 审查 → 可迭代 |
| **管线设计** | 6 种输出模式各有固定 pipeline 模板 | 动态 skills 组合：`pipeline_design.md` 由 agent 现场设计，skills 按需加载 |
| **迭代模型** | 单次走完 pipeline，失败最多重试 3 次（Stage 9→7 loop） | 多轮迭代：单轮中断恢复 + 跨轮次持续优化，`result.json` 支持 `revision_needed` |
| **审查机制** | 3 个固定 sub-agent（A/B/C） | 审查前置：pipeline 中每个阶段可按需声明审查点 + 验收清单，不限于固定 3 个 |
| **偏好管理** | per-cluster learnings overlay 文件 | 三层偏好：任务级（[B] 采集）→ 课程级（overlay 沉淀）→ 用户级（Claude Code memory） |
| **提交行为** | `result.json` 状态永远 `draft_ready`，从不自动提交 | 同样不自动提交，但 [E] 检查点提供更丰富的选项（提交 / 我先看 / 迭代修改） |

### AutoStudy 不照搬的部分

- **固定 pipeline 模板**：Copilot 为每种输出模式定义了固定阶段序列。AutoStudy 选择更灵活的动态组合，因为 Claude Code 的 agent 能力足够强，不需要预先枚举所有可能。
- **单次 batch execute**：Copilot 的 `canvas-execute` 一次性分发所有审批项。AutoStudy 的 `do-homework` 只处理用户选择的单项，保留助手式的节奏控制。
- **Humanizer（硬编码强制）**：Copilot 在 essay/doc_prose 模式中硬编码调用 humanizer。AutoStudy 保留 humanizer 作为可选后处理 skill（用户在 [B] 要求或 pipeline_design.md 声明时才调用），不作为默认行为。
- **Stop hook 强锁**：Copilot 用 Stop hook 阻止 session 在未完成所有作业时结束。AutoStudy 是助手，不应该阻止用户随时离开。
- **重 overlay 体系**：Copilot 每种 skill 配套 100-300 行 overlay。AutoStudy 用三层偏好体系替代（渐进实现），不需要用户手动编写 overlay。

---

## 7. Copilot per-type Skill 深度管线分析

对 Copilot 六个具体 skill 的完整管线做了深度阅读。每个 skill 有独立的
侦查、生成、验证流程，差异很大。AutoStudy 的 skills 架构设计
（见 `docs/skills-architecture-spec.md`）从中提取了可借鉴的模式，
同时避免了固定 per-type pipeline 的僵化。

| Skill | 管线阶段数 | 侦查方式 | 生成核心 | 验证机制 | 独特设计 |
|---|---|---|---|---|---|
| canvas-generic | 11 (Stage 0-11) | 全量 Stage 1-5 | 通用管线 (Stage 6-7) | Sub-agent B (验证清单) + C (覆盖度) | 三层子代理审查，验证重试循环 |
| canvas-ics33 (代码) | 9 (Stage 1-9) | 定向 (overlay 的 `spec_source`) | test-first implement (逐 feature) | identifier grounding + numeric constraints + re-clone verify | process_humanize 重写 git 历史，constraints.md 提取 |
| canvas-essay (长文) | 8 (Step 1-8) | 定向 (walk PDFs/modules) | outline → body → revise | 字数 + 引用数 + plagiarism risk + voice register | persona profile (MBTI → derived_vector)，humanizer 后处理 |
| canvas-reading-annotation (标注) | 6+ (Stage 1-6.5) | 定向 (overlay 的 homework_module_id) | PDF 物理操作 (PyMuPDF) | 6-check gate (line fill, color family, page count) | color rubric + voice register (B1-B2) |
| canvas-zybooks (数学) | 7 (Step 1-7) | 解析 Canvas description HTML table | API 调题 → LLM 解题 → LaTeX 渲染 | 子题数 + 无占位符泄漏 | zyBook API + JWT，不提交到 Canvas |
| canvas-inside (quiz) | ~7 | — | 4-agent arbitration per question | 3 层强制执行机制 | paced submission (人类节奏模拟)，strategic miss |

### 跨 Skill 共有模式（AutoStudy 已借鉴）

1. **Research before improvise**：当 spec 不符合已知模板时，spawn 2-3 个
   parallel agents 做深度调查。AutoStudy 的实现：skill Guidance 中的
   "不确定时先调查"原则。

2. **Post-delivery self-audit**：结构验证通过后，强制 spawn 1 个 audit
   agent 做 spec-vs-deliverable 语义 diff。AutoStudy 的实现：统一的
   sub-agent 审查框架，在 `pipeline_design.md` 的 stage 中按需声明
   `review: true`。

3. **约束提取 + 可量化验证**：生成前从 spec 提取 testable constraints，
   生成后用机械检查验证。AutoStudy 的实现：`pipeline_design.md` 的
   `## Constraints` + 每个 skill 的 Self-check。

4. **Overlay 加载**：每个 skill 第一步读 overlay 获取课程级知识。
   AutoStudy 的实现：三层偏好系统（当前只实现了任务级，通过
   `alignment_brief.md` 和 `pipeline_design.md` stage 声明传递）。

5. **Stage-by-stage 校准**：首次运行逐阶段审查。AutoStudy 的实现：
   do-homework [B] 的 alignment brief + pipeline_design.md 的 review 声明。
