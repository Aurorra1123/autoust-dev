# Execution Architecture Spec — Stage-per-Agent + Independent Review

> 2026-06-04 · AutoStudy 执行架构升级设计
> 合入 M3.5-ITERATION + M3.5-SUB-AGENT-REVIEW
> 前置：M3.5-SKILLS-ARCHITECTURE (passing), M3.5-DYNAMIC-PIPELINE (passing)

---

## 1. 问题定义

### 1.1 模型系统性糊弄

单 agent 执行模式存在三个结构性缺陷，导致产出质量系统性低于预期：

**缺陷 1: 上下文衰减**

主代理做到第 N 个 stage 时，第 1 个 stage 加载的 skill 质量标准已被上下文挤压到边缘。后续 stage 越做越松，self-check 清单形同虚设。

**缺陷 2: 自审自批**

同一个 agent 既执行又审查，等于自己给自己打分。实际表现：agent 报告"notebook 已执行"，但轨迹显示从未调用 `nbconvert --execute`。审查和执行必须是独立的 agent，才有真正的制衡。

**缺陷 3: 瀑布式质量衰减**

假设每个 stage 质量为 80%，4 个 stage 叠加后最终质量仅 41%（0.8^4）。主代理感知不到衰减过程，因为每一步它都觉得"还行"。

### 1.2 实际证据

| 项目 | 糊弄表现 | 后果 |
|------|----------|------|
| DSAA2011（重构前） | notebook 构建了 45 cells 但从未执行 | 报告引用编造的 accuracy/AUC |
| DSAA2011（Round 1） | 检查了 tectonic 但跳过 xelatex 直接跳 fpdf2 | 4 次盲目试错 |
| UCUG1505 | sketch.js 340 行从未在浏览器运行 | 不知道 audio API 是否可用 |
| 两个项目共性问题 | Write 被沙箱拒后用 heredoc 绕过 | 产出文件绕过了状态追踪 |

### 1.3 根因结论

**单 agent 模式无法保证原子步骤质量。** 即使 skill 文件写得再好，agent 的上下文有限性和自我审查的天然倾向，都会导致"差不多就行"的结果。必须通过架构层面的强制机制来保证质量。

---

## 2. 架构设计

### 2.1 三角色模型

```
┌──────────────────────────────────────────────────────┐
│ 协调者 (Coordinator)                                  │
│ 即用户的 Claude Code session 主代理                    │
│                                                       │
│ 职责：                                                │
│   - 读取 skill 文件，设计 pipeline_design.md           │
│   - 用户交互 [B] 侦查汇报 / [E] 交付审核              │
│   - 为每个 stage 构造 brief + 派执行子代理             │
│   - 为每个 stage 派独立审查子代理                      │
│   - 审查不过时注入修复建议、重跑执行子代理             │
│   - 读执行摘要和审查 verdict，不读产出全文             │
│                                                       │
│ 不做：                                                │
│   - 不写任何 draft/ 文件                               │
│   - 不执行代码/notebook                                │
│   - 不渲染 PDF                                        │
│   - 不撰写报告/文档                                    │
├──────────────────────────────────────────────────────┤
│ 执行者 (Executor) — 子代理，每个 stage 一个            │
│                                                       │
│ 职责：                                                │
│   - 读 stage brief + workbench 文件                   │
│   - 按需读 skill 文件（brief 中指定路径）              │
│   - 完成原子任务，写产出到 draft/                      │
│   - 返回执行摘要（状态 + 产出路径 + 关键指标）         │
│                                                       │
│ 约束：                                                │
│   - 子代理上下文独立，不继承协调者历史                 │
│   - 只能读 brief 中明确列出的文件                      │
│   - 只能写 brief 中明确声明的产出路径                  │
├──────────────────────────────────────────────────────┤
│ 审查者 (Reviewer) — 子代理，独立于执行者               │
│                                                       │
│ 职责：                                                │
│   - 读产出文件 + stage quality_criteria               │
│   - 独立判断 PASS / FAIL                              │
│   - FAIL 时给出具体 fix_suggestions                   │
│   - 返回结构化 verdict                                │
│                                                       │
│ 约束：                                                │
│   - 不执行任何修改（只读）                             │
│   - 不读执行者的内部过程，只读最终产出                 │
│   - verdict 必须基于可验证的标准，不接受"看起来还行"   │
└──────────────────────────────────────────────────────┘
```

### 2.2 执行流程

```
协调者 ─── 读 skill → 设计 pipeline_design.md → [B] 用户交互

对于 pipeline 中的每个 Stage N：

  ┌─ Step 1: 写 brief
  │  协调者写 stage_N_brief.md 到 workbench
  │  包含：任务描述、tool 指导、quality_criteria、reads/writes、
  │       skill 文件路径、上下文摘要
  │
  ├─ Step 2: 派执行子代理
  │  Agent({
  │    prompt: "你是执行 agent。brief 在: ${brief_path}。
  │             先读 brief，再读 brief 中指定的文件。
  │             产出到: ${output_paths}。
  │             返回简短摘要。",
  │  })
  │
  ├─ Step 3: 派审查子代理
  │  Agent({
  │    prompt: "你是审查 agent。检查 ${output_paths} 的质量。
  │             quality_criteria 在: ${brief_path} 的 quality_criteria 段。
  │             返回 JSON: { verdict: PASS|FAIL,
  │                          evidence: [...],
  │                          fix_suggestions: [...] }",
  │  })
  │
  ├─ Step 4: 判断
  │  if verdict == PASS → 进入 Stage N+1
  │  if verdict == FAIL && retries < max_retries:
  │    写 stage_N_fix.md（含 fix_suggestions）
  │    回到 Step 2（执行子代理读 fix brief 重跑）
  │  if retries >= max_retries:
  │    标记 stage 状态为 NEEDS_HUMAN_REVIEW
  │    写入 human_review_items
  │
  └─ Step 5: 继续
     进入下一个 Stage

全部 Stage 完成 → [E] 用户审核 → 提交
```

### 2.3 交接机制（混合模式）

**协调者 → 执行子代理**:
```
prompt 核心指令（< 500 tokens）:
  "你是 {tool_name} 执行 agent。
   Stage brief: {brief_path}
   产出路径: {output_paths}
   先读 brief 再执行。完成后返回摘要。"

stage_N_brief.md（写文件，不限长度）:
  - 任务描述和约束（从 pipeline_design.md 提取）
  - skill 指导摘要（从 skill 文件提取关键段）
  - quality_criteria（可量化标准）
  - reads 列表（子代理应该读哪些文件）
  - writes 列表（子代理应该写哪些文件）
  - 上下文片段（前序 stage 的关键输出摘要）
```

**执行子代理 → 协调者**:
```
返回文本摘要（< 200 tokens）:
  "Stage 1 完成。
   产出: draft/notebook.ipynb (1.8MB)
   关键指标: 25/25 cells executed, 0 errors, 12 plots generated
   需要注意: 第 15 cell 有 RuntimeWarning (非致命)"
```

**协调者 → 审查子代理**:
```
prompt 审查指令（< 300 tokens）:
  "你是独立审查 agent。
   检查: {output_paths}
   标准: 见 brief 中的 quality_criteria
   返回 JSON verdict。"

审查者自行读产出文件 + brief，独立判断。
```

**审查子代理 → 协调者**:
```
结构化 verdict (JSON):
{
  "verdict": "PASS",
  "evidence": [
    "notebook 执行了 25/25 cells",
    "0 errors in execution",
    "accuracy = 0.78 (from cell 20 output)"
  ]
}

或

{
  "verdict": "FAIL",
  "evidence": [
    "cell 15 output is empty",
    "accuracy not found in any cell output"
  ],
  "fix_suggestions": [
    "cell 15 使用了未定义的变量 data_clean",
    "accuracy 应在 classification report 后输出"
  ]
}
```

---

## 3. 文件格式

### 3.1 Stage Brief 格式

```markdown
# Stage Brief: {stage_name}

## Task
{从 pipeline_design.md 提取的 stage 描述}

## Tool Guidance
{从对应 skill 文件提取的关键指导（非全文，只取与当前 stage 相关的段）}

## Quality Criteria
{可量化标准，审查子代理按此检查}
- [ ] criterion 1: ...
- [ ] criterion 2: ...

## Reads
- {file_path_1}: {用途说明}
- {file_path_2}: {用途说明}

## Writes
- {file_path_1}: {预期内容说明}

## Context From Previous Stages
{前序 stage 的关键输出摘要，避免子代理读完整的前序产出}

## Fix Suggestions (仅重跑时存在)
{审查子代理返回的 fix_suggestions，协调者原样注入}
```

### 3.2 pipeline_design.md 格式升级

在现有格式基础上增加 `delegate`、`review`、`review_focus`、`max_retries`、`quality_criteria` 字段：

```markdown
## Stages

### Stage 1 — Notebook
- tool: code-writer
- delegate: sub-agent
- review: true
- review_focus:
    - notebook 实际执行无错误
    - 所有 code cell 有非空输出
    - 数据指标来自真实运行结果
- max_retries: 3
- lang: python
- type: notebook
- reads: spec.md, investigation/rubric.md
- writes: draft/project.ipynb
- quality_criteria:
    - execution: 0 errors via nbconvert --execute
    - completeness: all code cells have output
    - data_integrity: metrics come from actual execution, not estimates
  verify: notebook executes without errors

### Stage 2 — Requirements
- tool: code-writer (inline)
- delegate: coordinator
- review: false
- reads: draft/project.ipynb
- writes: draft/requirements.txt

### Stage 3 — Report
- tool: writing-helper
- delegate: sub-agent
- review: true
- review_focus:
    - 所有 rubric 条目被覆盖
    - 数据指标与 notebook 执行结果一致
    - 无 [CITATION NEEDED] / [TODO] 占位符
- max_retries: 2
- post-process: humanize
- reads: spec.md, investigation/rubric.md, draft/project.ipynb outputs
- writes: draft/report.md
- quality_criteria:
    - coverage: every rubric criterion addressed
    - data_grounding: all numbers traceable to notebook output
    - no_placeholders: zero [TODO]/[PROBLEM N]/[此处填入] markers
    - word_count: within ±10% of requirement

### Stage 4 — PDF Rendering
- tool: pdf-renderer
- delegate: sub-agent
- review: true
- review_focus:
    - PDF 有效（%PDF magic bytes）
    - 页数和大小满足 min_quality
- max_retries: 3
- reads: draft/report.md
- writes: draft/report.pdf
- quality_criteria:
    - valid: magic bytes %PDF
    - size: > 10KB
    - pages: >= 5
    - chinese: CJK characters render correctly (not tofu)
```

### 3.3 Stage Result 格式

每个 stage 完成后，协调者（或子代理）写入 stage result：

```json
{
  "stage": 1,
  "status": "pass",
  "executor_summary": "25/25 cells executed, 0 errors, 12 plots",
  "reviewer_verdict": "PASS",
  "reviewer_evidence": ["..."],
  "retries": 0,
  "output_files": ["draft/project.ipynb"],
  "human_review_flagged": false
}
```

或审查不通过时：

```json
{
  "stage": 1,
  "status": "fix_applied",
  "executor_summary": "fixed cell 15, re-executed",
  "reviewer_verdict": "PASS",
  "reviewer_evidence": ["cell 15 now has output", "accuracy = 0.78 verified"],
  "retries": 1,
  "fix_suggestions_applied": ["cell 15 used undefined variable data_clean"]
}
```

---

## 4. 与现有架构的关系

### 4.1 受影响的文件

| 文件 | 变更 |
|------|------|
| `do-homework.md` | 重写为纯协调者模式，[D] 执行改为派子代理 |
| `task-orchestrator.md` | 重写为子代理调度器，负责 brief 构造和审查循环 |
| `pipeline_design.md` | 格式升级，增加 delegate/review/quality_criteria |
| 各 tool skill 文件 | 增加 `execution_guidance` 段（给执行子代理的指导摘要） |
| 新增: 审查 prompt 模板 | `sub-skills/prompts/reviewer-prompt.md` |
| 新增: brief 构造逻辑 | 在 task-orchestrator.md 中定义 |

### 4.2 不受影响的部分

- Skill 文件的 Contract/Guidance/Appendices/Self-check 结构不变
- 渐进式加载机制（_index.md → Layer 2 → Layer 3）不变
- 路径发现规则（spec §2.4）不变
- 侦查阶段（Stage 1-5）不变（仍然由主代理做，因为涉及用户交互）
- canvascli 命令接口不变
- result.json 状态机制不变（增加 stage_results 数组）

### 4.3 与 M3.5 项的合入

| 原计划项 | 合入方式 |
|----------|----------|
| M3.5-ITERATION | 审查修复循环天然支持多轮迭代。跨 session 恢复通过 result.json + brief 存档实现 |
| M3.5-SUB-AGENT-REVIEW | 本设计的审查者角色就是具体实现 |
| M3.5-PREFERENCE-SYSTEM | 偏好通过 brief 文件传递给子代理，不依赖主代理上下文。三层偏好体系不变 |

---

## 5. 侦查阶段的位置

侦查阶段（Canvas Generic Stage 1-5）**不派子代理**，仍然由协调者直接执行。原因：

1. 侦查需要调用 canvascli（需要 session 认证状态）
2. 侦查涉及 [B] 用户交互（补充信息）
3. 侦查产物是 spec.md + investigation/ + pipeline_design.md，是后续所有 stage 的基础
4. 侦查本身不涉及"糊弄"问题（数据来自 Canvas，不是模型生成）

子代理分工从 pipeline_design.md 完成后的 [C] 执行阶段开始。

---

## 6. 预期收益

| 问题 | 解决方式 | 预期效果 |
|------|----------|----------|
| 上下文衰减 | 每个子代理独立上下文，fresh start | 每步质量标准被完整执行 |
| 自审自批 | 执行者和审查者是独立子代理 | 审查真正发现执行缺陷 |
| 瀑布衰减 | 每步 PASS 才往下走 | 原子质量有保障，雪球不会滚大 |
| 模型糊弄 | 审查者检查实际产出 | notebook 未执行？直接 FAIL |
| 上下文不够用 | 协调者只读摘要 | 主代理上下文留给协调决策 |
| 任务时长 | 子代理并行/串行灵活调度 | 不受单 agent 上下文窗口限制 |

---

## 7. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 子代理 Write 被沙箱拦截（P5） | brief 中明确建议用 Bash heredoc 备选 |
| 审查子代理过于宽松 | quality_criteria 必须可量化、可验证，不接受"看起来还行" |
| 子代理 token 消耗大 | 简单 stage (delegate: coordinator) 不派子代理 |
| max_retries 打满仍 FAIL | 降级为 NEEDS_HUMAN_REVIEW，不强制继续 |
| brief 构造消耗协调者上下文 | brief 模板化，从 pipeline_design.md 自动提取 |
| 子代理之间缺乏上下文共享 | 前序 stage 摘要通过 brief 的 "Context From Previous Stages" 传递 |

---

## 8. 实现路线（先设计后实现）

### Phase 1: 基础设施（预计 2-3 个文件修改）
- 定义 stage brief 格式
- 定义审查 prompt 模板
- 定义 stage result 格式
- 在一个项目上手动模拟流程验证

### Phase 2: 协调者改造（预计 3-4 个文件修改）
- do-homework.md 重写为纯协调者
- task-orchestrator.md 重写为子代理调度器
- pipeline_design.md 格式升级

### Phase 3: 审查循环（预计 2-3 个文件修改）
- 审查子代理 prompt 模板
- 修复建议注入机制
- max_retries 逻辑

### Phase 4: 端到端验证
- 在 DSAA2011 和 UCUG1505 上验证新架构
- 对比新架构 vs 旧架构的产出质量
