# Skills Architecture Spec

> AutoStudy 的 Skills 架构设计文档。定义 post-reconnaissance 阶段的
> pipeline 设计、skill 加载机制、skill 内容规范和组合模式。
>
> 本文档是 M3.5+ 开发的核心设计参考。所有 skill 文件的编写和修改
> 都应遵循本文档中确立的原则。

Runtime handoff rules live in `docs/runtime-agent-protocol.md`. This file
defines skill structure and pipeline design conventions; the runtime protocol
defines how the Main Agent turns those plans into stage briefs, results,
reviews, and final verification evidence.

---

## 1. 设计定位

AutoStudy 的 skills 不是固定流水线脚本，而是**领域专业知识的结构化补充**。

模型本身已经知道怎么写代码、写文章、渲染 PDF。Skill 告诉模型的是：
"在我们这个项目中，怎么做才是对的。"——项目规范、质量标准、自检清单、
与其他 skill 的协作方式。

这与 Canvas Copilot 的做法有本质区别：

| 维度 | Canvas Copilot | AutoStudy |
|---|---|---|
| Skill 是什么 | 完整流水线说明书（400-500 行） | 领域指导 + 按需加载的附录 |
| 管线来源 | 固定模板 + overlay 参数 | agent 根据侦查结果现场设计 |
| 课程适配 | 重 overlay（100-300 行 YAML） | 三层偏好体系（渐进实现） |
| 组合方式 | 固定 pipeline 内硬编码调用 | skill 按条件动态发现和加载 |

---

## 2. 渐进式加载机制

### 2.1 三层发现

```
Layer 1: _index.md
  只暴露顶层 skill 入口（code-writer, writing-helper, ...）
  不列出子技能/附录

Layer 2: 父级 skill 文件
  读 code-writer.md 后才知道有 code-writer-python.md、code-writer-cpp.md
  读 writing-helper.md 后才知道有 writing-helper-essay.md、humanizer.md

Layer 3: 子技能/附录文件
  按需加载，只在父级 skill 读完并判断需要后读取
```

### 2.2 为什么不能平铺

如果 `_index.md` 直接列出 `writing-helper-essay`，agent 可能会：
- 跳过 `writing-helper.md` 的核心指导
- 直接读 essay 附录，缺少引用规范、语言规则、自检清单
- 结果是只拿到类型结构，丢掉了质量标准

每一层都必须在上一层提供的上下文中才能被正确理解。

### 2.3 _index.md 的角色

`_index.md` 是**能力菜单**，不是路由表。它帮助 agent 在写
`pipeline_design.md` 时知道有哪些可用工具：

- 每个 skill 的一行描述
- 输入/输出契约
- 适用场景提示
- **不包含**子技能/附录/语言规范

agent 看菜单点菜，根据任务需要自由组合。不预设固定链。

### 2.4 路径发现规则（解决 P0）

Agent 的工作目录在 `data/homework/<COURSE>/<HWID>/`，而 skill 文件
在仓库根下。agent 必须能从工作目录找到 skill 文件。

**方案：层级推导 + git rev-parse 双保险**

```text
推导规则：
  - WORK_DIR = data/homework/<COURSE>/<HWID>/
  - REPO_ROOT = 从 WORK_DIR 向上 3 级目录
  - SKILLS_DIR = REPO_ROOT/sub-skills/tools/
  - _INDEX = SKILLS_DIR/_index.md
```

保险层：如果推导结果无效，使用 `git -C "$WORK_DIR" rev-parse --show-toplevel`
获取真实仓库根。

在 `do-homework.md [A2]` 创建工作台时，将 `REPO_ROOT` 绝对路径写入
`pipeline_design.md` 的 metadata 头。`task-orchestrator.md` Step 1 优先从
pipeline_design.md 读取 REPO_ROOT，fallback 到层级推导，再 fallback 到
`git rev-parse`。

**子代理环境注意（P5）**：Write 工具在子代理沙箱中可能被限制。
当 skill 需要写文件时，如果 Write 工具被拒绝，使用
`Bash + cat > file <<'EOF'` heredoc 作为替代方案。

---

## 3. Skill 文件结构

### 3.1 统一模板

每个 skill 遵循以下结构：

```markdown
---
name: <skill-name>
description: <一句话能力说明>
---

# <skill-name>

## Contract
- reads: [从 workbench 读什么文件]
- writes: [写到 workbench 什么文件]
- preconditions: [前置条件]

## Guidance
[核心领域指导——告诉 agent 我们这里怎么做才是对的]

## Appendices（按需加载）
[列出可用的附录文件，agent 根据上下文判断是否需要读取]

## Post-processing
[完成后可选的后续步骤，可嵌套调用其他 skill]

## Self-check
[自检清单]
```

### 3.2 子技能/附录文件

附录文件遵循以下结构：

```markdown
---
name: <parent>-<specific>
description: <一句话说明，标注被哪个父级 skill 加载>
---

# <parent>-<specific>

被 `<parent>` 按需加载。不要直接从 `_index.md` 跳到这里。

## [具体的语言/类型/场景规范]
```

---

## 4. Skill 组合模式

### 4.1 嵌套调用

skill 可以在 Post-processing 中引用其他 skill。但不是硬编码调用，
而是**按条件建议**：

```markdown
## Post-processing
- 如果 pipeline_design.md 声明了 `post-process: humanize`，
  或用户在 [B] 要求降低 AI 味道，则读取 humanizer.md 并执行
- 否则跳过
```

调用决策基于三个信息源：
1. `pipeline_design.md` 中当前 stage 的声明
2. 用户在 do-homework [B] 的补充要求
3. skill 自身的判断（如检测到长文输出）

### 4.2 共享模式

以下模式是跨 skill 通用的，在各自 skill 文件中以引用方式描述：

**约束提取（生成前）**：从 spec.md 提取可量化约束，
写入 `pipeline_design.md` 的 constraints 部分。

**自检（生成后）**：每个 skill 完成后按自检清单逐项验证。

**Sub-agent 审查（可选）**：pipeline_design.md 中按需声明
"此 stage 后需要审查"。当 review 启用时，Main Agent 先运行 spec
compliance review，对比 artifact、`spec.md`、rubric、user notes 和 stage
brief；spec compliance 通过后，才运行 artifact-specific quality review。
审查输出写入 `stage_reviews/`。

### 4.3 文件传递

skill 之间通过 workbench 文件协作，不直接调用：

```
code-writer 写出 draft/src/algorithm.py
    ↓ (文件传递)
writing-helper 读取 draft/src/ 中的运行结果
    ↓ (文件传递)
pdf-renderer 读取 draft/report.md 渲染成 draft/report.pdf
```

这保证了：
- 每个 skill 独立可测试
- 失败可断点续跑
- 用户可中途接管某一步

---

## 5. Pipeline Design 格式

`pipeline_design.md` 由 do-homework [C] 在侦查 + 用户确认
`alignment_brief.md` 后写。
格式示例：

```markdown
# Pipeline: DSAA2011 Project

## Output
- mode: mixed (code + doc_prose + package)
- deliverables: [notebook.ipynb, report.pdf, presentation.pdf, requirements.txt]

## Constraints
- [从 spec 提取的可量化约束]
- 代码必须包含 dropout 相关实验
- 报告不少于 2000 字
- notebook 必须能从头运行

## Stages

### Stage 1 — 核心算法实现
- id: stage_01_notebook
- tool: sub-skills/tools/code-writer.md
- delegate: subagent
- lang: python
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - spec.md
  - investigation/rubric.md
  - investigation/alignment_brief.md
  - references/project_announce.pdf
- writes:
  - draft/notebook.ipynb
  - draft/requirements.txt
  - draft/metrics.json
- quality_criteria:
  - notebook 能从 clean kernel 从头运行无报错
  - 报告引用的 metrics 必须来自实际执行输出
- human_blockers:
  - dataset choice if the spec allows multiple datasets and user has not chosen

### Stage 2 — 实验报告
- id: stage_02_report
- tool: sub-skills/tools/writing-helper.md
- delegate: subagent
- type: report
- lang: en
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - spec.md
  - investigation/rubric.md
  - investigation/alignment_brief.md
  - draft/metrics.json
- writes:
  - draft/report.md
- quality_criteria:
  - 覆盖 rubric 每个评分点
  - 数值结论来自 draft/metrics.json 或可追溯 reference
- human_blockers:
  - group member names if required by the assignment

### Stage 3 — 渲染 PDF
- id: stage_03_pdf
- tool: sub-skills/tools/pdf-renderer.md
- delegate: subagent
- review:
  - spec_compliance: false
  - quality: true
- max_retries: 1
- reads:
  - draft/report.md
  - investigation/alignment_brief.md
- writes:
  - draft/report.pdf
- quality_criteria:
  - PDF exists and magic bytes are %PDF
  - file size and page count meet min_quality
- fallback: sequential renderer fallback declared by pdf-renderer.md
- min_quality: PDF > 10KB, pages >= 5

### Stage 4 — Presentation
- id: stage_04_slides
- tool: sub-skills/tools/slide-maker.md
- delegate: subagent
- review:
  - spec_compliance: true
  - quality: true
- max_retries: 1
- reads:
  - draft/report.md
  - spec.md
  - investigation/alignment_brief.md
- writes:
  - draft/slides.pdf
- quality_criteria:
  - slide count and format match assignment deliverable requirements

### Final Review
- 全量交付物审查（spec vs deliverable）
- 所有 constraints 逐项验证
```

每个 stage 可包含：
- `id`：稳定 stage id，例如 `stage_01_report`
- `tool`：调用的顶层 skill
- `delegate`：`main-agent` 或 `subagent`
- `lang`：覆盖默认语言（code-writer 读取）
- `type`：覆盖默认类型（writing-helper 读取）
- `constraints`：从 spec 提取的约束
- `review.spec_compliance`：true/false，是否审查 artifact 是否答对题
- `review.quality`：true/false，spec compliance 通过后是否做质量审查
- `max_retries`：进入 human review 前允许重跑 executor 的次数
- `quality_criteria`：executor 和 reviewer 都使用的可量化检查
- `human_blockers`：stage 前后需要用户在 alignment loop 或最终复核中处理的信息
- `post-process`：可选后处理步骤（如 humanize）
- `fallback`：首选工具不可用时的回退方案（防止反复试错）
- `min_quality`：最低质量门槛（如 `PDF > 10KB`、`pages >= 5`）

---

## 6. 偏好系统集成（三层偏好）

偏好在三个层级管理，skill 文件提供默认值，偏好系统逐层覆盖：

| 层级 | 来源 | 存储位置 | 状态 |
|---|---|---|---|
| **任务级** | do-homework [B] 对齐循环 | `investigation/alignment_brief.md` -> `pipeline_design.md` stage 声明 | ✅ 当前实现方式 |
| **课程级** | 跨作业积累的课程偏好 | `data/course-overrides/<COURSE>.md` | 🔲 待实现 |
| **用户级** | 用户主动声明或推断 | Claude Code 项目 memory | 🔲 待实现 |

### 6.1 任务级偏好（当前实现）

agent 在写 `pipeline_design.md` 时，根据侦查结果和 [B] 结束时确认的
`investigation/alignment_brief.md`，在每个 stage 中声明具体参数：

```
Stage 1: code-writer, lang: python
Stage 2: writing-helper, type: report, lang: en
```

这些信息来自：
- spec.md 的内容（作业要求什么语言、什么格式）
- `alignment_brief.md` 的 confirmed decisions、delegated decisions、
  non-negotiables 和 open final-review items
- `user_notes.md` 的多轮对话记录只作为过程证据；它不替代最终
  `alignment_brief.md`

### 6.2 课程级偏好（待实现）

当三层偏好系统实现后：
- 如果 `data/course-overrides/DSAA2012.md` 存在并声明了
  `default_framework: pytorch`，code-writer 读取并优先使用
- 如果用户在 [B] 补充了冲突信息，任务级覆盖课程级
- 课程偏好在首次作业侦查后逐步积累

### 6.3 用户级偏好（待实现）

- 存储在 `~/.claude/projects/.../memory/`
- 跨课程持久（如"默认中文输出"、"我的代码风格偏好"）
- 用户级 > 课程级 > 任务级（越具体优先级越高）

### 6.4 默认值

skill 文件中声明的默认值：

| 偏好项 | 默认值 | 覆盖方式 |
|---|---|---|
| 代码语言 | Python | pipeline_design.md stage.lang |
| 环境管理 | uv | course-overrides 或 user memory |
| 写作语言 | 英文 | pipeline_design.md stage.lang |
| 写作语体 | 学术正式 | course-overrides 或 pipeline_design.md |
| 引用格式 | APA | spec 要求 或 course-overrides |
| PDF 引擎 | tectonic | course-overrides |

---

## 7. 当前文件结构

```text
sub-skills/tools/
├── _index.md                     # 能力菜单（只列顶层 skill）
├── code-writer.md                # 代码生成：通用原则 + 加载语言附录
├── code-writer-python.md         # Python 规范：uv / pytest / 项目结构
├── code-writer-cpp.md            # C++ 规范：cmake / src+include（待写）
├── writing-helper.md             # 写作：通用原则 + 加载类型附录
├── writing-helper-essay.md       # essay 结构规范（待写）
├── writing-helper-report.md      # lab/project report 结构规范（待写）
├── humanizer.md                  # 降低 AI 味道（待写）
├── pdf-renderer.md               # Markdown → PDF（已稳定）
├── slide-maker.md                # Slides（已有）
├── paper-search.md               # 文献搜索（已有）
├── figure-maker.md               # 数据可视化（已有）
├── test-runner.md                # 测试执行（已有）
├── assignment-recon.md          # Canvas Generic 侦查（已有）
└── canvascli-api.md              # Canvas CLI 参考（已有）
```

标注"待写"的文件是按本文档设计需要新建的。现有文件（code-writer.md、
writing-helper.md 等）需要按本文档的模板重构。

---

## 8. 验证和审查

### 8.1 约束提取（生成前）

agent 在写 `pipeline_design.md` 时从 spec 提取可量化约束。
约束写入每个 stage 的 `constraints` 或顶层 `## Constraints`。

通用约束提取模式：
- grep spec 中的数字限制（"no more than"、"at least"、"exactly"）
- 列出 spec 中提到的必须实现的函数/类/接口
- 标记 spec 中的禁止项（"must not"、"forbidden"、"do not"）
- 标记 spec 中的示例输入/输出

### 8.2 自检（每个 skill 完成后）

每个 skill 有自己的 Self-check 清单。orchestrator 在 stage 完成后
验证清单中的每一项。

### 8.3 Sub-agent 审查（可选，按 stage 声明）

当 `pipeline_design.md` 的 stage 声明 `review.spec_compliance: true` 或
`review.quality: true` 时，Main Agent 生成 reviewer brief 并按顺序审查：

```text
1. spec compliance reviewer
   输入: stage brief + artifact + spec.md + rubric.md + user notes
   输出: stage_reviews/<stage_id>_spec_review.json
   目的: 判断 artifact 是否答对题、覆盖 deliverables/rubric/constraints

2. quality reviewer
   前提: spec compliance verdict == PASS
   输入: stage brief + artifact + tool self-check / quality_criteria
   输出: stage_reviews/<stage_id>_quality_review.json
   目的: 判断 artifact 是否高质量、可运行、可渲染、证据扎实
```

如果 spec compliance `FAIL` 且 `max_retries` 未耗尽，Main Agent 根据
`fix_suggestions` 写 fix brief 并重跑 executor。Quality review 永远不能早于
spec compliance。审查内容由 stage 的 `quality_criteria`、skill 的 Self-check、
以及 `docs/runtime-agent-protocol.md` 的 reviewer contract 共同决定。

---

## 9. 与 Canvas Copilot 的对照

本文档的设计参考了 Canvas Copilot 六个 per-type skill 的深度分析。
以下是我们学了什么、改了什么：

### 9.1 借鉴的机制

| Copilot 模式 | AutoStudy 适配 |
|---|---|
| Research before improvise | skill Guidance 中的"不确定时先调查"原则 |
| Post-delivery self-audit | 统一的 sub-agent 审查框架，按 stage 声明 |
| 约束提取 + 可量化验证 | pipeline_design.md 的 constraints 提取 + skill Self-check |
| Overlay 加载（课程级知识） | 三层偏好系统（渐进实现） |
| identifier grounding（代码标识符必须有 spec 依据） | code-writer Guidance 中的命名对齐原则 |

### 9.2 不照搬的部分

| Copilot 做法 | 不照搬的理由 |
|---|---|
| 固定 pipeline 模板（per-type 6 种） | 动态 skills 组合（原则 2） |
| canvas-humanizer（降低 AI 检测信号） | 与"agent 负责脏活，用户负责审核"定位矛盾；但作为可选后处理保留 |
| process_humanize（伪造 git 历史） | 学术诚信红线 |
| 重 overlay（100-300 行 YAML/课程） | 三层偏好体系更灵活 |
| canvas-inside 4-agent arbitration | Quiz 自动提交伦理风险 |

### 9.3 Copilot per-type skill 管线对比

以下是对 Copilot 六个具体 skill 的完整管线分析，作为 AutoStudy
skill 设计的参考：

| Skill | 侦查 | 生成 | 验证 | 独特机制 |
|---|---|---|---|---|
| canvas-generic | 全量 Stage 1-5 | 通用管线 (Stage 6-7) | Sub-agent B/C | 三层子代理审查 |
| canvas-ics33 (代码) | 定向 (overlay 告诉 spec 在哪) | test-first implement | identifier grounding + re-clone verify | process_humanize 重写 git 历史 |
| canvas-essay (长文) | 定向 (walk PDFs/modules) | outline→body→revise | 字数+引用+plagiarism | persona profile + humanizer |
| canvas-reading-annotation | 定向 (overlay 的 module_id) | PDF 物理操作 (PyMuPDF) | 6-check gate (line fill, color family) | color rubric + voice register |
| canvas-zybooks (数学) | 解析 Canvas table | API 调题→LLM 解题→LaTeX | 子题数+无占位符泄漏 | zyBook API + JWT |
| canvas-inside (quiz) | — | 4-agent arbitration | 3 层强制执行 | paced submission (人类节奏模拟) |

AutoStudy 的统一侦查（generic Stage 1-5）覆盖了所有类型的侦查需求。
生成和验证阶段通过 skill 的 Guidance + 附录提供领域指导。

---

## 10. 开发优先级

基于本文档的设计，skill 相关的开发优先级：

1. **重构 code-writer.md** — 按新模板重写，新建 code-writer-python.md
2. **重构 writing-helper.md** — 按新模板重写，新建 writing-helper-report.md
3. **更新 _index.md** — 移除固定路由表，改为能力菜单
4. **新建 humanizer.md** — 可选后处理 skill
5. **新建 writing-helper-essay.md** — essay 类型附录
6. **新建 code-writer-cpp.md** — C++ 附录（按需）
7. **在真实作业上验证新 skill 架构** — 选一个 mixed 任务跑通完整 flow
