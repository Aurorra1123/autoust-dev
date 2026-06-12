# AutoStudy 开发方向讨论：从 AutoPku 对标中找到我们的路径

> **受众**：AutoStudy 项目负责人
> **目的**：基于对 AutoPku（北大）的深度拆解，讨论 AutoStudy 的下一步开发方向——特别是"哪些场景用固定流水线、哪些场景坚持动态管线"
> **状态**：构思阶段，开放讨论

---

## 一、先说结论

AutoPku 和 AutoStudy 表面上做的是同一件事（学业自动化），但底层设计哲学完全不同。两种选择各有道理，而我们应该走的是**混合路线**：

- **作业场景**（do-homework）→ 坚持**动态管线**，因为 HKUST(GZ) 的作业类型差异太大，固定流水线兜不住
- **重复性学习场景**（收集课件→解析PDF→做笔记、批量生成slides等）→ 引入**固定流水线**，因为这些流程高度可预测，调好了就是稳定产出

下面展开说为什么。

---

## 二、AutoPku 到底是怎么做的——以三个非作业技能为例

### 2.1 write-notes（课程笔记）：教科书式的固定并行流水线

```
扫描 lectures/ 目录 → 用户选范围/详细度/额外需求
→ 为每个 PDF 并行 spawn Writer Agent（每个 Agent 独立读 PDF + 提取 + 写笔记）
→ 汇总索引 notes/README.md
→ pandoc + Lua filter 统一渲染为 PDF
```

**关键特点**：
- 每节课的笔记生成是**完全同构**的——同样的输入（课件PDF）、同样的输出（带 callout 的 Markdown）、同样的提取规则（保留定义/定理/证明，去掉轶事/装饰）
- 并行策略极其自然：10 个课件就 spawn 10 个 Agent，各干各的
- 每个 Writer Agent 的 prompt 模板是固定的（定义了保留什么、删除什么、用多少 callout、概念图用 mermaid）
- 最后的渲染也是统一的 pandoc 方案

**这就是一条调试好的流水线**。只要课件格式不发生根本变化，这条线就能稳定跑。

### 2.2 write-paper（论文写作）：固定 Phase + 章节并行

```
Phase 1: 获取论文要求
Phase 2: 用户确认题目/格式/字数/参考文献数量
Phase 3: 生成大纲（单个 Agent）
Phase 4: 按章节并行 spawn Writer Agent（每个章节一个 Agent）
Phase 4.5: 图片获取（可选，image-handler 工具）
Phase 5: 渲染输出（LaTeX / Word 双模式）
```

**关键特点**：
- Phase 1-3 是串行的（收集需求 → 确认 → 大纲），这和我们的侦查阶段类似
- Phase 4 是并行的（每个章节独立写作），且每个 Writer Agent 的 prompt 里**注入了大纲中对应章节的摘要**，确保各章节风格统一
- Phase 5 有双模式输出：LaTeX（pkucourse_paper_template + xelatex 编译两次）或 Word（python-docx 生成，去除生成痕迹）
- 图片处理（Phase 4.5）是一个条件分支，有图就走，没图就跳

**本质**：这仍然是固定流水线，只不过在"章节并行"这个点做了加速。论文写作的流程本身是高度可预测的——选题→大纲→正文→图片→排版→输出，几乎每篇课程论文都走这个路径。

### 2.3 make-slides（幻灯片生成）：最复杂的固定流水线

```
Phase 1: 数据源检测（课件PDF / 笔记 / 论文 / 手动输入）→ 用户确认
Phase 2: 内容提取（Agent，根据数据源类型用 pdf-reader 或直接读 markdown）
Phase 3: 大纲生成（Agent，设计 3-6 个章节，每个章节 2-4 个要点）
Phase 4: Agent Team 并行生成各章节的 Typst 页面代码
Phase 4.5: 图片获取（可选）
Phase 5: 组装（slide-renderer 工具，用 pkusli Typst 模板）+ typst compile
Phase 6: 用户确认
```

**关键特点**：
- 有条件分支（数据源不同 → Phase 2 的提取方式不同），但**整体流程固定**
- Phase 4 的并行策略很聪明：每个章节一个 Agent，prompt 里包含该章节的大纲摘要 + pkusli 的 8 种页面函数文档，Agent 直接输出 Typst 代码片段
- 最后由 slide-renderer 统一组装（生成 main.typ、插入各章节代码、typst compile）
- 有缓存机制：pkusli 模板 git clone 一次后缓存，避免重复下载

### 2.4 小结：AutoPku 的 Agent 使用模式

看完所有五个 task，AutoPku 的模式非常清晰：

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| **单 Agent 串行** | 一个 Agent 按步骤执行 | sync-notices（简单任务） |
| **按实体并行** | 每个课程/章节/题目独立 Agent | write-notes（每节课）、write-paper Phase 4（每章节）、make-slides Phase 4（每章节） |
| **角色分工** | 不同角色 Agent 各司其职 | do-homework（Parser→Solver→Writer→Renderer→Submitter） |

**但无论哪种模式，流程都是预设的**。Agent 不需要"思考"下一步该做什么，它只需要按照 Skill 文件里写好的步骤执行。

---

## 三、两种设计哲学的本质差异

### 3.1 AutoPku：调试好的流水线

```
用户意图 → 固定路由到某个 task skill → 预设的 Phase 序列
→ 各 Phase 由固定角色的 Agent 执行 → Agent 之间通过 SendMessage 或直接返回通信
```

**Agent 在这里的作用**：
1. **并行加速**：10节课的笔记同时写、5个章节同时生成 → 省时间
2. **角色隔离**：Parser 只管解析、Solver 只管解题 → 每个 Agent 的 context 更干净
3. **质量一致**：每个 Agent 用同一个 prompt 模板 → 产出风格统一

**不做什么**：
- 不动态决定"这个作业应该走哪条线"
- 不做深度侦查来理解任务需求
- 不根据 rubric 动态调整执行策略

**为什么这在北大行得通**：北大本科的作业类型相对固定——数理课有习题集、文科课有论文/读书报告、PPT汇报。这些流程可以枚举，流水线可以预先调好。

### 3.2 AutoStudy：动态管线 + 审查修复

```
用户意图 → 侦查阶段（5 Stage 深度侦察）
→ 质量门控（review_a.json）→ 用户确认侦查结果
→ 动态设计 pipeline_design.md → 逐 Stage 执行 + 每步验证
→ 用户审查交付物 → 提交
```

**子代理在这里的作用**：
1. **节省上下文**：渐进式三层加载，agent 不需要一次读完全部 skill → 避免 context 膨胀
2. **审查隔离**：独立审查 agent 做 spec 与交付物的语义 diff → 避免自己审自己的盲区
3. **断点续跑**：每个 Stage 的产物通过文件传递，中断后从断点恢复

**为什么 HKUST(GZ) 需要这么做**：
- 作业类型差异极大——一篇 paper critique、一份编程实验报告、一组数学证明、一个 group presentation slides、一个 mixed（代码+报告+slides）可能同时出现
- Canvas 上的作业描述质量参差不齐——有些老师把要求写在 assignment page，有些藏在 syllabus 里，有些在 module 的 external URL 里，需要 5 Stage 侦查才能摸清
- 评分标准（rubric）也差异很大——有些有 Canvas rubric，有些只是文字描述，有些压根没有

**如果我们也用固定流水线**：要么穷举所有可能的作业类型（不可维护），要么强行把所有作业塞进少数几个模板（牺牲质量）。

### 3.3 一句话总结差异

| | AutoPku | AutoStudy |
|---|---------|-----------|
| **Agent 的角色** | 流水线工人（按预定义步骤执行） | 现场工程师（侦查→设计→执行→验证） |
| **对模型的依赖** | 中等（需要理解 Skill 文件，但步骤已明确） | 高（需要理解作业需求、动态设计管线、判断质量） |
| **稳定性来源** | 预调试的流程 + 固定角色 prompt | 侦查充分性 + 审查修复循环 + 约束验证 |
| **灵活性来源** | 条件分支（数据源不同走不同子路径） | pipeline_design.md 完全自由组合 |

---

## 四、我们的方向：混合架构

### 4.1 核心判断

> **作业的异构性决定了我们需要动态管线，但学习的重复性意味着固定流水线更高效。**

具体来说：

| 场景 | 流程可预测性 | 推荐模式 | 理由 |
|------|-------------|----------|------|
| **完成作业** | 低（每次都不同） | 动态管线 ✅ | 作业类型、需求来源、交付格式、评分标准差异太大 |
| **课程笔记** | 高（每节课同构） | 固定流水线 🆕 | 输入固定（课件PDF），输出固定（结构化笔记），流程可枚举 |
| **批量下载整理资料** | 高 | 固定流水线 🆕 | 纯机械操作，无需模型决策 |
| **生成复习 slides** | 中高 | 半固定流水线 🆕 | 大部分流程固定（提取→大纲→生成），但数据源可能不同 |
| **论文写作辅助** | 中 | 动态管线 ✅ | 写作要求差异大，但可以提供常见管线形状作为参考模板 |

### 4.2 新增固定流水线场景设计

#### 场景 A：课程笔记生成（write-course-notes）

这完全可以直接借鉴 AutoPku 的 write-notes：

```
sync-status 扫描课程 → 发现课件/资料
→ 用户选择课程 + 笔记范围（全部/指定周次）+ 详细程度
→ 从 Canvas 下载课件 PDF 到 data/notes/<COURSE>/lectures/
→ 为每个课件并行 spawn Note Agent：
    - 读取 PDF（pdf-reader 工具）
    - 按模板提取核心内容（保留：定义/定理/证明/结论，删除：轶事/装饰/重复）
    - 生成带 callout 和 mermaid 概念图的 Markdown
→ 汇总索引 notes/README.md
→ 可选：pandoc 渲染为 PDF
```

**为什么这里适合固定流水线**：
- 输入同构（课件 PDF）
- 输出同构（结构化 Markdown 笔记）
- 每个 Agent 的 prompt 可以预调好（哪些保留、哪些删除、callout 风格）
- 并行策略天然（每个课件独立）
- 不需要"理解作业需求"这种高认知负担的任务

**和 do-homework 的区别**：这里不需要 5 Stage 侦查、不需要 pipeline_design.md、不需要审查修复循环。就像工厂流水线，调好了就一直跑。

#### 场景 B：批量收集整理课程资料（collect-materials）

```
sync-status 扫描 → 发现未下载的课件/资料
→ 用户确认下载范围
→ 并行下载到 data/materials/<COURSE>/（按周次/类型组织）
→ 生成资料清单 materials/INDEX.md
```

更简单的纯机械操作，甚至不需要 Agent 的认知能力，只需要 canvascli 的批量调用。但可以用 Agent 做一些附加价值的事（比如自动给 PDF 重命名、识别资料类型分类整理）。

#### 场景 C：复习 Slides 生成（make-review-slides）

```
用户选择课程 → 数据源检测（已有笔记/课件PDF）
→ 固定流程：提取内容 → 生成大纲 → 按章节并行生成 slides
→ 渲染输出
```

半固定——整体流程固定，但数据源不同时提取方式略有差异。可以借鉴 AutoPku make-slides 的 Phase 设计，但保留少量条件分支。

### 4.3 do-homework 不变——但可以增加"管线形状快捷方式"

do-homework 的动态管线设计保持不变，但可以增加一个优化：

在 `[C] Design Pipeline` 阶段，如果侦查结果表明这是一个"典型场景"（比如纯 paper critique），可以让 agent 参考**预定义的管线形状模板**（如 `paper-shape.md`），而不是从零开始设计。

这相当于：
- 80% 的常见场景：用预调试的管线形状，稳定高效
- 20% 的特殊场景：自由组合，灵活应对

这和 AutoPku 的区别在于：**我们的固定模板是"参考"而非"强制"**。agent 发现模板不合适时可以偏离。

---

## 五、具体实施建议

### 5.1 近期（M3.5 收尾 → M4 之前）

1. **完成 M3.5 当前工作**：task-orchestrator 结构化摘要、侦查汇报优化、skills 架构重构
2. **新增 `write-course-notes` skill**（固定流水线）：
   - 放在 `sub-skills/tasks/write-course-notes.md`
   - 在 `_index.md` 注册
   - 参考 AutoPku 的 write-notes 流程设计
   - 在 `skill.md` 添加路由（"帮我写XX课的笔记"）
3. **新增 `collect-materials` skill**（简单固定流程）：
   - 放在 `sub-skills/tasks/collect-materials.md`
   - 主要调用 canvascli 批量下载 + 简单整理

### 5.2 中期（M4 学习助手）

4. **课程笔记生成可以成为 M4 学习助手的基础**：有了每节课的结构化笔记，Socratic questioning 助手就有素材了
5. **增加"管线形状快捷方式"**：在 pipeline_design 阶段引入常见形状模板

### 5.3 远期（M5 多平台）

6. **借鉴 AutoPku 的运行时适配层**：实现 `_detect.md` + `create-agent.md` 模式
7. **固定流水线场景最先适配多平台**（因为流程固定，适配成本低）

---

## 六、从 AutoPku 可以直接借鉴的具体设计

| 借鉴点 | AutoPku 的做法 | 我们怎么用 |
|--------|---------------|-----------|
| **角色 Agent prompt 模板** | `agent-helpers.md` 预定义 Coordinator/Parser/Solver/Writer/Submitter 的 prompt | 为 write-course-notes 设计 Note Writer Agent 的 prompt 模板，确保笔记风格一致 |
| **并行策略** | 按实体并行（每课件/每章节一个 Agent） | write-course-notes 直接复用——每个课件一个 Agent |
| **运行时检测** | `_detect.md` 四种平台自动检测 | M5 多平台适配时的参考设计 |
| **统一 Agent 创建** | `create-agent.md` 封装平台差异 | 值得在引入多平台时参考 |
| **PDF 渲染缓存** | pkusli 模板 git clone 一次后缓存 | 我们的 pdf-renderer 可以引入类似缓存机制 |
| **条件分支文档化** | 每个 task skill 里明确写"如果有X就做Y，否则做Z" | 值得在 write-course-notes 中效仿，使条件逻辑透明 |

---

## 七、风险与开放问题

### 7.1 需要讨论的问题

1. **固定流水线的维护成本**：每新增一个固定流程 skill，就多一份需要维护的"调试好的流水线"。如果 Canvas 接口变了、课件格式变了，需要更新。是否值得为每个重复性场景都建固定流水线？

2. **固定 vs 动态的边界**：论文写作辅助（write-paper）到底是放固定还是动态？AutoPku 用固定的，但他们只面向北大。HKUST(GZ) 的论文要求差异多大？如果 80% 都差不多，可以用固定+条件分支。

3. **用户预期管理**：如果用户看到笔记生成很快很稳（固定流水线），会不会对 do-homework 的速度有更高预期？（动态管线必然更慢，因为要侦查+设计）

4. **M4 学习助手和笔记的关系**：write-course-notes 生成的笔记应该是什么粒度？直接服务于 M4 的 Socratic questioning，还是更粗粒度的复习资料？

5. **并行 Agent 的 token 成本**：固定流水线的并行策略（10 个课件同时 spawn Agent）在 Claude Code 下的 token 消耗如何？AutoPku 的用户可能不在意（北大用户群体？），但我们需要考虑成本。

### 7.2 我的倾向

- 先做 `write-course-notes`（固定流水线），这是最高 ROI 的新功能——需求明确、流程可枚举、AutoPku 有现成参考
- `collect-materials` 作为 sync-status 的自然延伸，不单独建 skill，而是在 sync-status 中增加"批量下载"选项
- do-homework 的动态管线保持不变，但增加常见管线形状作为参考模板
- M4 基于 write-course-notes 的产出来构建，形成"笔记生成 → 基于笔记的学习助手"的产品闭环

---

## 八、总结

AutoPku 给了我们一个很好的对标参考。它的核心洞察是：**对于流程可预测的学业任务，固定流水线 + 并行 Agent 是最稳定高效的方案**。我们不应该因为选择了动态管线就拒绝固定流水线——两者服务的是不同场景。

我们的架构已经为这种混合预留了空间：`_index.md` 是能力菜单，`skill.md` 是路由入口。新增固定流水线 skill 只需要在 `_index.md` 注册一行、在 `skill.md` 加一条路由，不会影响现有的动态管线架构。

**一句话**：do-homework 继续走动态管线（因为作业异构），write-course-notes 走固定流水线（因为学习重复），两者在同一个 skill 系统中共存。
