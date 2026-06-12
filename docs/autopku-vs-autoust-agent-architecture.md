# AutoPku vs AutoStudy：Agent 架构对比分析

> **目标**：深入剖析 AutoPku 如何使用 agent 完成任务，并与 AutoStudy 当前设计做逐层对比，找出差异、优劣和可借鉴之处。

---

## 一、AutoPku 的 Agent 工作机制

### 1.1 核心理念：Skill 文件即程序

AutoPku **不写任何框架代码**。全部领域逻辑以 Markdown Skill 文件的形式存在，寄生于宿主 Agentic AI（Claude Code / Codex / Kimi Code CLI）。AI 读取这些 `.md` 文件后自行理解意图、执行命令。

```
用户自然语言 → skill.md（入口路由）→ task skill（执行流）→ tool skill（原子能力）
                                       ↕
                                 runtime 适配层（跨平台 Agent 创建）
```

### 1.2 三层目录结构

| 层次 | 目录 | 职责 | 文件数 |
|------|------|------|--------|
| **任务层** | `sub-skills/tasks/` | 5 个端到端业务流程 | 5 |
| **工具层** | `sub-skills/tools/` | 可复用原子能力 | 6 |
| **运行时层** | `sub-skills/runtime/` | 跨平台 Agent 创建适配 | 5 |

### 1.3 运行时自动检测与适配

AutoPku 在 `runtime/_detect.md` 中定义了环境自动检测逻辑：

```python
if CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:  RUNTIME = "claude"   # Agent() + SendMessage()
elif CODEX == "1":                         RUNTIME = "codex"    # native subagents
elif KIMI_CODE_CLI or which("kimi"):       RUNTIME = "kimi"     # Agent() + TaskList
else:                                      RUNTIME = "serial"   # 串行回退
```

所有 task skill 通过引用 `create-agent.md` 统一创建 Agent，**无需关心底层平台差异**。

### 1.4 五个任务流程详解

#### Task 1: `sync-notices` — 同步课程通知

```
检查 pku3b → 登录教学网 → 拉取数据 → 解析数据
→ 为每门课并行创建 Agent → 各自生成通知摘要
```

**Agent 策略**：每门课程一个独立 Agent，并行执行，各自创建目录、下载附件、生成 `通知摘要.md`。

#### Task 2: `do-homework` — 完成作业（最核心）

```
Phase 1: PDF 解析（parser agent）→ homework_parsed.json
Phase 2: 逐题解答（solver agent）→ answers.json
Phase 3: 文档生成（writer agent）→ .md
Phase 4: PDF 渲染（Markdown → HTML → Chrome Headless → PDF）
Phase 5: 教学网提交（pku3b a submit）
```

**关键安全机制**：
- 列出待交作业 → `AskUserQuestion` 让用户选择
- 二次确认后才执行
- 渲染完成后询问是否提交
- **禁止**自动选择最新作业、禁止未经确认直接提交

**角色 Agent 配置**（来自 `agent-helpers.md`）：

| 角色 | 职责 |
|------|------|
| Coordinator | 分配任务，汇总结果，协调 Phase 顺序 |
| PDF Parser | 代码间接解析 PDF（禁止直接读取） |
| Solver | 逐题解答，参考资料 |
| Writer | 格式化 Markdown 答案 |
| Renderer | Markdown → PDF |
| Portal Submitter | 提交到教学网 |

#### Task 3: `write-notes` — 撰写笔记

```
扫描课件 PDF → 用户确认范围/详细程度
→ 为每个 PDF 并行创建 Writer Agent
→ 各 Agent 解析 + 提取核心内容
→ 生成带 callout 和 mermaid 图的 Markdown
→ pandoc + Lua filter 渲染
```

#### Task 4: `write-paper` — 撰写论文

```
Phase 1: 获取要求
Phase 2: 用户确认题目/格式/字数
Phase 3: 生成大纲（Agent）
Phase 4: 正文生成（Agent Team 按章节并行）
Phase 4.5: 图片获取（可选）
Phase 5: 渲染输出（LaTeX / Word 双模式）
```

#### Task 5: `make-slides` — 生成幻灯片

```
Phase 1: 数据源检测 → Phase 2: 内容提取（Agent）
→ Phase 3: 大纲生成（Agent）→ Phase 4: Agent Team 并行生成各章节 Typst
→ Phase 5: 组装渲染（pkusli 模板 + typst compile）
```

### 1.5 Agent 通信方式（因平台而异）

| 平台 | 创建方式 | 通信方式 |
|------|----------|----------|
| Claude Code | `Agent()` + `SendMessage()` | Agent 间直接通信 |
| Kimi | `Agent(subagent_type="coder")` | 结果直接返回父代理 |
| Codex | 自然语言描述 | return values |
| Fallback | 串行 | 无通信，顺序执行 |

---

## 二、AutoStudy 的 Agent 工作机制

### 2.1 核心理念：动态管线 + 审查修复循环

AutoStudy 同样以 Markdown Skill 文件寄生在宿主 agent 上，但引入了两个核心差异：

1. **动态管线设计**：不固定 Phase 顺序，而是由 agent 根据具体作业需求现场设计 `pipeline_design.md`
2. **工作台文件契约**：所有中间产物通过标准化文件结构传递，而非 Agent 间直接通信

### 2.2 三层目录结构

| 层次 | 职责 | 核心文件 |
|------|------|----------|
| **任务层** | 端到端流程 | `sync-status.md`, `do-homework.md`, `task-orchestrator.md` |
| **工具索引层** | 能力发现 | `sub-skills/tools/_index.md` |
| **工具层** | 原子能力 | `assignment-recon.md`, `pdf-renderer.md`, `writing-helper.md` 等 |

### 2.3 核心工作流：do-homework 六步

```
[A] Build Workbench（自动）
    A1: 解析标识符（plan item → course_id/assignment_id）
    A2: 创建工作台目录
    A3: Canvas Generic Reconnaissance（Stage 1-5 侦查）
    A4: 侦查质量门控
[B] Recon Summary + 用户补充 ← 用户交互点 #1
[C] Design Pipeline（自动，动态组合技能）
[D] Orchestrator Runs（自动，逐 Stage 执行 + 验证）
[E] Draft Review + 提交确认 ← 用户交互点 #2
[F] Submit（仅用户确认后）
```

### 2.4 工作台结构（文件契约核心）

```
data/homework/<COURSE>/<HWID>/
  canvas/               -- Canvas CLI JSON 快照（只读）
  spec.md               -- 标准化侦查报告
  references/           -- 下载的参考资料
  investigation/
    rubric.md           -- 评分标准
    review_a.json       -- 侦查充分性审查
    pipeline_design.md  -- 动态管线设计（核心契约）
  draft/                -- 产出物
  result.json           -- 流程状态收据
```

**关键差异**：AutoStudy 的 Agent 之间**不直接通信**，而是通过这个标准化目录结构中的文件来传递产物。每个工具独立可测试，失败可断点续跑。

### 2.5 动态管线设计

AutoStudy 不预设固定的 Phase 序列，而是：

1. 读入 `spec.md` + `rubric.md` + `review_a.json` + 用户补充信息
2. 查阅 `_index.md` 能力菜单
3. **现场组合**需要的技能，写入 `pipeline_design.md`
4. `task-orchestrator` 按 `pipeline_design.md` 逐 Stage 执行

这意味着同样都是"做作业"，一份编程作业和一份论文作业的管线形状完全不同。

---

## 三、逐维度对比

### 3.1 架构哲学

| 维度 | AutoPku | AutoStudy |
|------|---------|-----------|
| **设计哲学** | 固定流程 + 角色 Agent | 动态管线 + 文件契约 |
| **流程定义** | 每个 task 有预定义的 Phase 序列 | agent 现场设计 pipeline_design.md |
| **Agent 通信** | Agent 间直接通信（SendMessage） | 通过工作台文件间接传递 |
| **错误恢复** | 未明确设计 | 断点续跑，result.json 记录状态 |
| **适配范围** | 北大教学网（单一平台） | HKUST(GZ) Canvas + 未来多平台 |

### 3.2 Agent 使用模式

| 维度 | AutoPku | AutoStudy |
|------|---------|-----------|
| **Agent 创建** | 统一接口 `create-agent.md`，按角色分配 prompt | 宿主 agent 自行决策，无统一创建接口 |
| **并行策略** | 按实体并行（每门课/每章节一个 Agent） | 目前主要串行，task-orchestrator 逐 Stage 执行 |
| **角色定义** | `agent-helpers.md` 预定义 5 种角色 prompt | 无预定义角色，agent 根据上下文自行承担 |
| **运行时适配** | 4 种平台（Claude/Codex/Kimi/串行）自动检测 | 目前仅 Claude Code，多平台待开发 |
| **子代理审查** | 无明确机制 | 设计了审查前置机制（M3.5+ 开发中） |

### 3.3 任务流程对比

以最核心的**完成作业**为例：

#### AutoPku: do-homework（线性 Phase）

```
用户选作业 → [Phase 1: 解析PDF] → [Phase 2: 解题] → [Phase 3: 写文档]
→ [Phase 4: 渲染PDF] → [Phase 5: 提交] → 用户确认
```

- **流程固定**：永远走 5 个 Phase
- **角色明确**：每个 Phase 由固定角色的 Agent 执行
- **并行场景**：主要在 Phase 2（多题可并行）和论文的章节并行

#### AutoStudy: do-homework（动态管线）

```
用户选作业 → [A: 侦查工作台] → [B: 用户确认侦查结果]
→ [C: 动态设计管线] → [D: 逐Stage执行+验证] → [E: 用户审查+确认提交]
→ [F: 提交]
```

- **流程动态**：pipeline_design.md 由 agent 现场设计，不同类型作业有不同管线
- **侦查先行**：5 阶段深度侦查在执行前完成，确保信息充分
- **质量门控**：`review_a.json` 审查侦查充分性，不通过则补充
- **产物验证**：每个 Stage 产出的文件有验证（PDF magic bytes、page count 等）

### 3.4 数据获取层

| 维度 | AutoPku | AutoStudy |
|------|---------|-----------|
| **工具** | `pku3b`（独立 CLI 工具） | `canvascli`（独立 pip 包） |
| **输出格式** | 纯文本 + ANSI 颜色码（需正则解析） | JSON（结构化，无需解析） |
| **登录方式** | expect 脚本处理 TTY | Playwright SSO + cookie 持久化 |
| **数据层边界** | pku3b 是数据层，skill 是应用层 | canvascli 是数据层，skill 是应用层 |

### 3.5 安全与用户控制

| 维度 | AutoPku | AutoStudy |
|------|---------|-----------|
| **用户交互点** | 每个关键步骤前确认 | 2 个固定检查点 [B] 和 [E] |
| **提交保护** | 禁止自动提交，必须用户确认 | 同样，仅用户确认后提交 |
| **可中断性** | 未明确设计 | 断点续跑，用户可中途接管某一步 |
| **偏好系统** | 无 | 三层偏好体系（任务级/课程级/用户级，待完善） |

### 3.6 技能加载机制

| 维度 | AutoPku | AutoStudy |
|------|---------|-----------|
| **发现方式** | 直接引用路径，全量加载 | 渐进式三层发现（_index → 父级 → 子级） |
| **模板结构** | 无统一模板 | Contract → Guidance → Appendices → Self-check |
| **能力菜单** | 无，靠 skill.md 人工路由 | `_index.md` 结构化能力发现 |

---

## 四、各自的优势与不足

### AutoPku 的优势

1. **多平台运行时适配**：已实现 Claude Code / Codex / Kimi / 串行四种模式，这是 AutoStudy 目前缺失的
2. **角色 Agent prompt 模板化**：`agent-helpers.md` 预定义了 5 种角色 prompt，确保每个 Agent 的行为一致可控
3. **统一 Agent 创建接口**：`create-agent.md` 封装了平台差异，task skill 无需关心底层
4. **并行策略明确**：按实体（课程/章节/题目）并行，策略清晰
5. **轻量直接**：没有过度设计，5 个 task 覆盖主要场景

### AutoPku 的不足

1. **流程固定**：每个 task 的 Phase 序列硬编码，无法根据具体作业类型动态调整
2. **无侦查阶段**：不像 AutoStudy 有 5 阶段深度侦查，可能导致信息不充分就开始执行
3. **无错误恢复**：没有 result.json 或类似的状态记录，中断后难以续跑
4. **数据解析脆弱**：pku3b 输出纯文本 + ANSI 码，正则解析容易出错
5. **技能加载全量**：没有渐进式发现机制，每次可能加载不需要的内容

### AutoStudy 的优势

1. **动态管线**：根据具体作业需求现场设计执行计划，灵活性高
2. **深度侦查**：5 阶段 Canvas Generic Reconnaissance 确保信息充分
3. **文件契约**：标准化工作台结构，Agent 通过文件传递产物，独立可测试
4. **错误恢复**：result.json 记录状态，支持断点续跑
5. **结构化数据**：canvascli 输出 JSON，无需正则解析
6. **渐进式加载**：三层技能发现，减少不必要的 context 消耗

### AutoStudy 的不足

1. **无多平台适配**：目前仅支持 Claude Code，运行时适配待开发
2. **无预定义角色 prompt**：没有像 `agent-helpers.md` 那样的角色模板，Agent 行为一致性依赖上下文
3. **并行能力弱**：目前 task-orchestrator 主要串行执行，未充分利用 Agent 并行
4. **复杂度高**：动态管线 + 工作台 + 侦查 + 审查，学习成本和维护成本都更高
5. **尚未完成**：M3.5 仍在开发中，部分设计还在纸上

---

## 五、可借鉴之处

### 从 AutoPku 借鉴到 AutoStudy

| 借鉴点 | 说明 | 优先级 |
|--------|------|--------|
| **运行时适配层** | 实现 `_detect.md` + `create-agent.md` 模式，为 M5 多平台做准备 | 高（M5 前置） |
| **角色 Agent prompt 模板** | 为 task-orchestrator 的各 Stage 预定义角色 prompt，提升一致性 | 中 |
| **并行策略文档化** | 明确"哪些 Stage 可并行"的策略，而非全串行 | 中 |
| **统一 Agent 创建封装** | 封装 `Agent()` 创建逻辑，使 pipeline 设计不受平台影响 | 高 |

### 从 AutoStudy 反哺到 AutoPku

| 可借鉴点 | 说明 |
|----------|------|
| **动态管线设计** | AutoPku 的固定 Phase 可以考虑引入 pipeline_design 模式 |
| **深度侦查** | 5 阶段侦察确保信息充分，减少执行阶段的信息不足 |
| **文件契约 + 状态记录** | 标准化工作台 + result.json 支持断点续跑 |
| **渐进式技能加载** | 减少全量加载的 context 浪费 |

---

## 六、总结

| | AutoPku | AutoStudy |
|---|---------|-----------|
| **一句话概括** | 固定流程 + 角色 Agent + 多平台适配 | 动态管线 + 文件契约 + 深度侦查 |
| **成熟度** | 功能完整，5 个 task 均可运行 | M3.5 开发中，核心功能 MVP 可用 |
| **适合场景** | 流程固定、类型统一的学业任务 | 类型多样、需求差异大的学业任务 |
| **设计取舍** | 简单直接，牺牲灵活性 | 灵活强大，牺牲简洁性 |

两个项目本质上是**同一个问题（学业自动化）的两种解法**：AutoPku 选择了"预定义流程 + 角色 Agent"的确定性路线，AutoStudy 选择了"动态管线 + 文件契约"的灵活性路线。两者各有所长，最佳的演进方向可能是**融合**——在 AutoStudy 的动态管线框架中引入 AutoPku 的角色 prompt 模板和运行时适配机制。
