# Canvas Pilot 项目设计发现与 AutoStudy 开发建议

> 基于 canvas_copilot（下称 Canvas Pilot）项目的深度调查，提炼出对 AutoStudy 有参考价值的设计思想。
> Canvas Pilot 是一个面向通用 Canvas 学校的作业自动化框架，定位与 AutoStudy 不同（通用 turnkey 产品 vs HKUST(GZ) 专用 skill），但在工程设计和架构思路上有不少值得借鉴的地方。
> 本文不建议照搬其架构，而是提炼思想、结合 AutoStudy 的 5 模块愿景和现有 ROADMAP 讨论后续开发方向。

---

## 1. 最值得参考的四个设计思想

### 1.1 深度 Spec 侦查

#### Canvas Pilot 的做法

Canvas Pilot 有一个叫 **canvas-generic** 的核心编排器。它的设计思路是：遇到任何作业，不急于动手，而是先做一轮完整的"侦查"，搞清楚到底要做什么，再决定怎么做。

具体来说，它的侦查分三步：

**第一步：从 Canvas 拉取所有可能相关的信息源。** 不只看作业页面的 description 和附件，还会：

- 读取课程的 **Front Page**（很多教授把作业要求写在课程首页）
- 遍历课程的 **Modules**（很多课程按周组织，作业 spec 散落在某个 module item 里）
- 获取 **Syllabus**（课程大纲，常包含评分标准和作业格式要求）
- 抓取 **外部链接**（有些作业 spec 链到教授个人网站或 GitHub）
- 下载所有 **附件**

这一步的产出是一个 `spec.md`，把从所有信息源找到的内容汇总到一起。

**第二步：搜索评分标准（Rubric）。** 不只在 Canvas API 提供的 rubric 字段里找，还会在 spec.md 里 grep 关键词、在 module/syllabus 里搜索、甚至去外部链接里找。四层搜索确保不遗漏。

**第三步：完整性审查。** 侦查完成后，会用一个 sub-agent 审查"我们搞清楚了到底要做什么吗？"——交付物类型明确吗？rubric 找到了吗？input 文件齐了吗？如果不完整，会自动补一轮侦查。

#### 对 AutoStudy 的启发

当前 AutoStudy 的 `problem-extractor` 只看 `assignment.json.description` 中的 HTML 里的附件链接，然后下载附件、提取文本。对于"作业要求都写在附件里"的场景（MVP 验证的 4 个场景）这够用了。

但从 AutoStudy.pdf 模块 1（Course Context Manager）和模块 5（Assignment & Academic Production）的愿景来看，我们需要的是更完整的课程材料获取能力。很多课程的作业 spec 不在附件里，而是在 Modules、Syllabus、课程首页、甚至外部链接中。特别是 HKUST(GZ) 的课程，教授们的组织习惯差异很大——有的把所有东西放在 assignment description 里，有的把 spec 写在 module page 里，有的链到自己的 Google Site。

#### 需要做什么

这涉及 **canvascli 的扩展**，因为 AutoStudy 的架构是 canvascli 独立仓库提供数据层，skill 层通过 shell out 调用。要实现深度侦查，需要两步：

**canvascli 侧**（新增命令或参数）：

- `canvascli modules --course-id <ID>` — 获取课程 module 列表和 module item 内容
- `canvascli front-page --course-id <ID>` — 获取课程首页内容
- `canvascli syllabus --course-id <ID>` — 获取课程大纲
- 可能还需要一个 `canvascli full-context --course-id <ID> --assignment-id <ID>` 的聚合命令，一次返回所有相关上下文

**AutoStudy skill 侧**（改造 `problem-extractor` 或 `do-homework` 的 [A3] 步骤）：

- 在现有的"从 description HTML 提取附件"之外，增加"从 modules/front-page/syllabus 补充上下文"的能力
- 产出可以还是 `problem.md`，但内容更完整——不只包含附件文本，还包含从其他信息源找到的相关内容
- 这对模块 3（Study Material Generator）也有直接价值——自动收集课程材料需要的就是同样的 Canvas 数据获取能力

---

### 1.2 侦查后的动态管线组合

#### 侦查之后，Canvas Pilot 做了什么

上节讲了 canvas-generic 怎么做侦查。侦查只是第一步，更关键的差异在侦查之后：**它不是查一张固定流水线表来决定怎么做，而是根据侦查结果动态组合执行步骤。**

具体来说，canvas-generic 在侦查完成后会做两件事：

**第一步：分类交付物形态。** 根据侦查到的 spec 内容，判断这个作业要产出的东西属于哪一类——是纯文本文档（doc_prose）、需要手写填空的 PDF（pdf_annotated）、需要打字回答的 PDF（pdf_typed）、代码项目（code）、表单问答（form_answers）、还是混合型（mixed，同时包含多种形态）。

**第二步：按形态动态生成执行步骤。** 不是从一个固定映射表里选 pipeline，而是根据分类结果和 rubric 要求，实时生成"先做什么、再做什么"的步骤列表。比如一个 mixed 类型的作业被分解为多个子 pipeline 独立执行，最后合并产出。

这个过程没有硬编码的 `if type == "paper": [search, write, render]`。每一步都是根据实际需要动态决定的。

#### 对比当前 AutoStudy 的方式

当前 `task-orchestrator.md` 的编排是**固定流水线**模式：

```
paper  → search_papers → make_figure → write_essay → render_pdf
slides → make_figure → render_slides
math   → write_essay → render_pdf
lab    → write_code → run_tests → write_essay → render_pdf
```

路由靠关键词启发式：`problem.md` 里出现 "essay" → paper，出现 "prove" → math，出现 "implement" → lab。然后查 `_index.md` 的 Scenario → Tool chain 表，走固定链。

这种模式在 MVP 阶段验证的 4 个场景（paper/slides/math/lab）里工作得很好，因为每个场景确实只有一种明确的交付物类型。但它有两个结构性弱点：

1. **复杂/混合任务无法处理。** 如果一个作业同时要求"搜集文献 + 写代码实验 + 撰写 report + 做 presentation"，当前的设计只能选择权重最高的一个类型（`mixed` 类型的处理方式是"pick the highest-weight one"），或者回退给用户。这意味着一个本可以自动化的复杂任务被简化了或放弃了。

2. **扩展新类型需要改表。** 每增加一种作业类型，都需要在 `_index.md` 加一条固定链、在 `task-orchestrator.md` 的启发式表里加一行映射。这是一种"枚举所有可能"的思路，随着类型增多会越来越难维护。

#### 建议的方向：从"固定流水线"到"技能包动态组合"

一个可能的改进方向是：**不预设固定 pipeline，而是把每个 tool 做成独立的"技能包"，让 orchestrator 根据任务需要动态组合。**

具体来说：

**保持现有的 tools 不变**——paper-search、figure-maker、writing-helper、pdf-renderer、code-writer、test-runner、slide-maker 各自仍然是独立的 skill 文件，各自定义清楚输入输出。

**改变 orchestrator 的编排方式**——从"查固定链"变成"根据 problem.md 分析这个任务需要哪些能力，然后按需调用"：

- 一个"搜集文献 + 代码实验 + report + slides"的作业，orchestrator 分析后生成执行计划：`[paper-search, code-writer, test-runner, writing-helper, slide-maker, pdf-renderer]`，依次调用，每一步的产出作为下一步的输入。
- 一个纯 math proof 作业，orchestrator 可能只需要：`[writing-helper, pdf-renderer]`。
- 一个只有代码的 lab，orchestrator 可能只需要：`[code-writer, test-runner]`。

这种方式的鲁棒性更强，因为：

- **不依赖关键词匹配到固定类型的映射**。即使作业类型没有被预定义过，orchestrator 仍然可以分析出"这个任务需要哪些能力"并调用对应的 tools。
- **自然支持混合任务**。不需要 special-case 处理 mixed 类型——每个子任务各自调用对应的 skill，组合在一起就是完整的 pipeline。
- **新增 tool 不需要改 orchestrator 的路由表**。只要新 tool 在 `_index.md` 注册了能力和输入输出，orchestrator 就能根据任务需要自动引入。

**可以配合 course-overrides 做课程级指引。** 不同的课程可能有不同的"常用技能组合"——比如某门课的作业几乎总是涉及"读 paper + 写 critique"，那可以在 `course-overrides.yaml` 里记录这个偏好，让 orchestrator 在分析时参考。这比为每门课写专用 pipeline 轻量得多。

#### 与现有架构的关系

这个改动是**渐进式**的，不需要一次性重写 orchestrator：

1. **M3 维持不变**。当前 4 条固定链继续工作，已有的 MVP 验证不受影响。
2. **可以先在 `task-orchestrator.md` 里加一个"自由组合"的 fallback 路径**——当启发式匹配不到任何固定类型时，不是直接问用户，而是尝试根据 problem.md 内容分析需要哪些 capabilities，然后按 `_index.md` 的 capability vocabulary 动态组合。
3. **后续逐步把固定链也迁移到动态组合模式**。当 fallback 路径验证成熟后，固定链可以逐渐退出，统一由动态编排接管。

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
- `do-homework` 的中间产物（`problem.md`、`task_profile.yaml`、各种 draft）存在 `data/homework/` 下，但没有一个统一的"这个作业做到哪了"的状态记录
- 跨 session 恢复靠 `agent-progress.md` 的自然语言交接日志，agent 需要读完整个文件才能推断状态

这不止影响 do-homework，更影响 AutoStudy.pdf 里的模块 2（Proactive Task Reminder）。要实现"DDL 提醒、优先级排序、进度追踪"，前提是有结构化的状态记录——否则 agent 无法判断"哪些作业已经做了、哪些还没开始、哪些快到期了"。

#### 建议怎么做

不需要像 Canvas Pilot 那么重（它还有 `_processed.json` 跨天 ledger、`plan.json` 审批门控等），但一个轻量的 `result.json` 就能解决大部分问题：

```json
{
  "course": "DSAA2043",
  "assignment_id": "12345",
  "status": "draft_ready",
  "problem_md": "data/homework/DSAA2043/12345/problem.md",
  "deliverables": ["data/homework/DSAA2043/12345/solution.pdf"],
  "updated_at": "2026-06-01T14:30:00Z"
}
```

放在 `data/homework/<COURSE>/<HWID>/result.json`，do-homework 完成时写，sync-status 时读。这样 sync-status 就能展示"这门课有 3 个作业已完成草稿、2 个未开始"，而不是只展示 DDL。

对于模块 2（Proactive Task Reminder），这个 `result.json` 加上 Canvas 的 submission 状态就是优先级排序的基础。

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

## 2. 结合 ROADMAP 与 AutoStudy 愿景的开发建议

以下建议嵌入到 AutoStudy 现有的 ROADMAP（M1-M5）和 AutoStudy.pdf 的 5 模块愿景中，按优先级排列。

### M3 收尾（当前 → 短期）

| 事项 | 来源 | 说明 |
|------|------|------|
| 清理被跟踪文档中的真实课程 ID | 安全审计 | `problem-extractor.md`、`canvascli-api.md` 等文件中的真实 ID 替换为占位符。为开源做准备。 |
| 加 2-3 个关键 hooks | 参考 Canvas Pilot | 提交前审计 + result.json schema 验证 + 泄漏检测。具体实施前可以先做一个，验证 hook 机制跑通。 |
| M3-SUBMIT 真实作业 E2E 验证 | feature-list | 当前 partially-verified，需要在一个真实未过期作业上跑通 3-step upload 全流程。 |

### M4 阶段：Interactive Tutor + Spec 侦查升级 + 动态编排

M4 在 ROADMAP 里是"反问式学习助手"，对应 AutoStudy.pdf 的模块 4。这个模块的核心是"根据课程内容主动出题、反问、追踪薄弱点"。同时 M4 也是升级编排能力的好时机——M3 的固定流水线已经验证了单个 tool 的可靠性，可以开始尝试动态组合。

| 事项 | 来源 | 说明 |
|------|------|------|
| canvascli 扩展：modules / front-page / syllabus 命令 | 参考 Canvas Pilot 的 spec 侦查 | 这是升级 problem-extractor 和实现模块 1（Course Context Manager）的数据层基础。没有这些数据，模块 3（Study Material Generator）也做不到"从 lecture slides / PDF / reading 自动生成课程笔记"。 |
| problem-extractor 升级 | 参考 canvas-generic Stage 1-3 | 在现有"从附件提取文本"之外，增加从 modules/front-page/syllabus 补充上下文的能力。产出还是 problem.md，但信息更完整。 |
| orchestrator 加 fallback 动态组合路径 | 参考 canvas-generic Stage 5-6 | 当启发式匹配不到固定类型时，分析 problem.md 需要哪些 capabilities，按 `_index.md` 的 capability vocabulary 动态组合 tools。不需要一次性替代固定链，先作为 fallback 验证。 |
| 轻量 result.json | 参考 Canvas Pilot 的状态管理 | 每个 do-homework 作业完成后写一个 result.json，记录状态和交付物路径。为 sync-status 的升级和模块 2 的进度追踪打基础。 |
| 轻量 course-overrides.yaml | 参考 Canvas Pilot 的 overlay 思想 | 不需要 Canvas Pilot 那么复杂的 overlay 机制，但一个简单的 `data/course-overrides.yaml` 可以记录"这门课的作业 spec 通常在哪里"、"这门课偏好的交付格式是什么"、"这门课常用的技能组合是什么"。当前不同课程用完全相同的 heuristics，但实际上教授们的组织习惯差异很大。 |

### M5 阶段：多平台 + 主动提醒

| 事项 | 来源 | 说明 |
|------|------|------|
| plan.json + _processed.json | 参考 Canvas Pilot 的跨 session 状态 | 让 sync-status 从"每次全量同步"变成"只看新增/变更的作业"。`_processed.json` 记录已处理过的作业，`plan.json` 记录当前轮次的计划。这是模块 2（Proactive Task Reminder）的基础。 |
| 轻量 cron 自动化 | 参考 Canvas Pilot 的 cron 框架 | Canvas Pilot 有 669 行的 cron 框架，我们不需要那么重。但一个简单的定时检查（"有没有新作业发布了"、"有没有快到期的作业还没开始"）是模块 2 的核心。可以用 Claude Code 的 `/loop` 或系统 cron 触发 sync-status。 |

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
| **scan/execute 架构分离** | AutoStudy 当前是单次任务模式，不需要 Canvas Pilot 那种批处理级分离 |

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

1. **深度侦查再动手** — 不只看附件，从 Canvas 的多个信息源完整获取作业 spec。这需要 canvascli 扩展，也是模块 1 和模块 3 的数据层基础。
2. **从固定流水线到技能包动态组合** — 不预设 paper/slides/math/lab 四条固定链，而是让 orchestrator 根据任务需要动态组合已有的 tools。鲁棒性更强，自然支持混合任务，扩展新 tool 不需要改路由表。
3. **结构化状态记录** — 用 JSON 文件（result.json）记录每个作业的状态，让 agent 跨 session 恢复，支撑模块 2 的进度追踪。
4. **关键路径代码强制** — 用 2-3 个 hooks 把最重要的安全规则从 prose 变成代码强制执行。

这些改动都是增量式的，不需要重构现有架构，可以逐步加入现有 ROADMAP 的各个阶段。最推荐的第一步是"技能包动态组合"——从给 orchestrator 加一个 fallback 路径开始，让它在匹配不到固定类型时尝试动态组合，验证通过后再逐步替代固定链。
