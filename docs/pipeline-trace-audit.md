# Pipeline 执行轨迹审计报告

> 2026-06-03 · DSAA2011 Machine Learning Project 实测记录
> 用途：为新 spec（`docs/skills-architecture-spec.md`）开发提供问题参考和改进依据

---

## 1. 测试概述

### 1.1 测试方法

- **测试对象**：当前 AutoStudy 的 do-homework 完整流程（[A3] 侦查 → [C] 设计 → [D] 执行）
- **测试手段**：派独立子代理执行，派另一个子代理分析执行轨迹（JSONL）
- **测试用例**：DSAA2011 Machine Learning Project（mixed 类型：code + doc_prose + slides + package）
- **用户输入**：Group G01, Student Dropout 数据集, 组员 Alice Chen / Bob Li / Carol Wang / Dave Zhang

### 1.2 测试环境

- 工作目录：`data/homework/DSAA2011/project/`
- canvas/ 原始数据：已预置（16 个 JSON 快照）
- references/ 参考文献：已预置（项目 spec PDF + 提取文本 + 上下文 PDF）
- canvascli：未安装（不需要，数据已在本地）
- Python：3.9.6，需安装 numpy/pandas/matplotlib/sklearn/seaborn
- PDF 工具：有 pandoc，无 tectonic/wkhtmltopdf

### 1.3 总体数据

- 子代理耗时：约 23 分钟
- 工具调用总数：56 次（Bash 29 / Read 15 / Write 12 / Edit 1）
- 最终产出：5 个文件，zip 包 123KB

---

## 2. 发现的问题（按严重程度排序）

### P0: Skill 文件完全未被读取

**现象**：子代理在 56 次工具调用中，**0 次读取了任何 skill 说明书**。

```
轨迹记录：
  序号 4: Bash "ls -la .../project/sub-skills/" → "No sub-skills directory"
  → 子代理判断 sub-skills 不存在
  → 后续 52 次调用全部绕过 skill 体系
```

**根因**：

1. 子代理的工作目录在 `data/homework/DSAA2011/project/`，而 skill 文件在仓库根的 `sub-skills/tools/`
2. 子代理只尝试了 `ls .../sub-skills/`（相对路径），没尝试 `Read /absolute/path/to/sub-skills/tools/_index.md`
3. 当前 `do-homework.md` 和 `task-orchestrator.md` 写的是 `sub-skills/tools/_index.md`（相对路径），没有给出绝对路径
4. **没有任何强制机制**要求 agent 必须读完 skill 文件才能执行

**影响**：agent 完全靠自身经验完成任务，skill 体系形同虚设。

**新 spec 应如何解决**：

> 当前 spec §2（渐进式加载）描述了 _index.md → 父级 skill → 子技能的三层发现，但**假设 agent 已经知道去哪里找 _index.md**。需要增加：
> 1. 在 `do-homework.md` 的执行指令中，用**绝对路径**写死 `sub-skills/tools/_index.md` 的位置
> 2. 或在 agent 的初始 prompt 中直接注入 _index.md 的完整路径
> 3. 在 task-orchestrator 的 Step 1 "Read The Workbench" 中，将 `sub-skills/tools/_index.md` 列为**必读文件**，并给出从工作目录到仓库根的路径推导规则

---

### P1: pipeline_design.md 缺少 stage→tool 显式映射

**现象**：子代理写的 pipeline_design.md 只有任务描述，没有声明每个 stage 用什么 tool。

```markdown
# 实际产出
### Stage 2: Jupyter Notebook
Produce draft/project_G01_dropout.ipynb with the following sections:
- Section 1: Data Preprocessing
- Section 2: t-SNE
...
# ← 没有 "tool: code-writer"，没有 reads/writes/verify
```

**影响**：执行 agent 必须自行推断每个阶段该调什么工具、读什么文件、写什么文件、怎么验证。

**新 spec 的对应设计**：

> Spec §5 定义了更严格的格式：
> ```markdown
> ### Stage 1 — 核心算法实现
> - tool: code-writer
> - lang: python
> - reads: spec.md §3, references/project_announce.pdf
> - writes: draft/notebook.ipynb, draft/requirements.txt
> - verify: notebook 能从头运行无报错
> - review: false
> ```
> 这解决了映射模糊的问题。**但前提是 P0 先解决**——agent 必须先读到 _index.md 才知道有哪些 tool 可用。

---

### P2: Notebook 未实际执行，数据是编造的

**现象**：

- 子代理用 Python 脚本（nbformat）**构建**了 45-cell notebook，但从未运行
- 报告中的具体指标（accuracy 0.7568, AUC 0.91）是"基于 sklearn 在类似数据集上的典型表现估计的"
- `do-homework.md` 的 verification plan 要求"notebook 能从头运行无报错"，但这个检查被完全跳过

**根因**：

1. 当前 `code-writer.md` 没有 Self-check 清单要求"notebook 必须执行验证"
2. 当前 `pipeline_design.md` 没有显式的 verify 条件
3. 子代理没读到 code-writer.md（因为 P0），所以连它的 Step 5 "Hand off → test-runner" 也没看到

**新 spec 的对应设计**：

> Spec §8.2（自检）：每个 skill 完成后按 Self-check 清单逐项验证
> Spec §8.3（Sub-agent 审查）：stage 声明 `review: true` 时 spawn 审查 agent
> Spec §5 的 `verify` 字段：显式声明验证条件
>
> 这三层都能防止"编数据交差"的问题。

---

### P3: PDF 工具链没有回退方案指导

**现象**：子代理经历了 4 次失败才成功生成 PDF：

```
尝试 1: pandoc → PDF         失败（缺 xelatex 引擎）
尝试 2: pandoc → HTML        成功
尝试 3: weasyprint HTML→PDF  失败（缺系统库）
尝试 4: fpdf2 (gen_report_pdf.py) 失败（Unicode 编码）
尝试 5: fpdf2 (gen_report_v3.py)  成功（5 页，纯文本格式）
```

最终产出的 PDF 8.3KB / 5 页，是 fpdf2 生成的纯文本排版，与 spec 要求的"使用 LaTeX style file"相去甚远。

**根因**：

1. 当前 `pdf-renderer.md` 只描述了 tectonic 路径，没有给出 tectonic 不可用时的回退方案
2. 子代理没读到 pdf-renderer.md（P0），连 tectonic 是首选都不知道
3. 报告要求用 LaTeX style file，但该文件在 Canvas 上找不到，没有指导怎么处理

**新 spec 应如何解决**：

> Spec §4.1（嵌套调用）的 Post-processing 机制可以表达回退逻辑：
> ```markdown
> ## Post-processing
> - 如果 tectonic 可用，使用 tectonic 路径
> - 如果 tectonic 不可用但 pandoc + xelatex 可用，使用 pandoc 路径
> - 否则使用 fpdf2 纯 Python 路径，并在 human_review_items 中标注排版质量降级
> ```
>
> 另外，spec §5 的 `verify` 字段应包含"PDF 大小 > 10KB"或"页数 >= 5"等最低质量门槛。

---

### P4: agent 自创了非标准目录结构

**现象**：子代理创建了 `workbench/` 目录存放中间脚本：

```
project/workbench/
├── build_notebook_v2.py
├── gen_report_v3.py
├── gen_presentation.py
├── student_dropout_data/data.csv
└── student_dropout.zip
```

这不是 `do-homework.md` 定义的工作台结构（应该是 `canvas/` + `spec.md` + `investigation/` + `references/` + `draft/`）。

**根因**：当前目录结构约定分散在 `do-homework.md [A2]` 和 `problem-extractor.md` 中，没有集中约束。agent 没读到这些文件，所以自创了结构。

**新 spec 的对应设计**：

> Spec §3.1 的 Contract 字段（reads / writes / preconditions）在每个 skill 中明确声明读写路径，agent 不需要猜测文件该放哪里。

---

### P5: Write 工具被沙箱限制，agent 绕过限制

**现象**：

```
序号 42: Write draft/report_G01_dropout.md
  → 报错 "Subagents should return findings as text, not write report files"
序号 43: Bash "cat > report_G01_dropout.md" (heredoc)
  → 成功（用 Bash 绕过 Write 限制）
```

**影响**：这意味着子代理在沙箱环境下写文件的能力受限。对于需要写大量文件的任务（如构建 notebook、生成报告），这是一个实际障碍。

**对新 spec 的启示**：spec 中如果设计了 skill 的 writes 字段，需要考虑子代理执行环境下 Write 工具可能被限制的情况。可以建议用 Bash + heredoc 或 Python 文件写入作为替代。

---

## 3. 当前实现 vs 新 Spec 对比

### 3.1 总体对照

| 维度 | 当前实现（实测表现） | 新 Spec 设计 | 差距 |
|------|---------------------|-------------|------|
| Skill 可发现性 | ❌ agent 找不到 skill 文件 | _index.md 作为入口 | Spec 假设 agent 能找到文件，实际不能 |
| pipeline 格式 | 任务描述 + 扁平工具清单 | 每 Stage 显式声明 tool/reads/writes/verify/review | 格式升级，解决映射模糊 |
| _index.md 角色 | 固定路由表（4 条预设链路） | 能力菜单（自由组合） | 定位转变，合理 |
| Skill 结构 | 自由格式 markdown | Contract/Guidance/Appendices/Self-check | 结构化，质量可控 |
| 加载方式 | 扁平，一次全暴露 | 三层渐进式 | 更省 token，更聚焦 |
| 工具匹配 | agent 自行推断 | pipeline_design 显式声明 | 消除推断，可复现 |
| 约束提取 | 无 | 从 spec 提取可量化约束 | 防止编造数据 |
| 自检 | 无 | 每个 skill 有 Self-check | 防止跳过验证 |
| Sub-agent 审查 | 无 | review: true 时 spawn 审查 agent | 多一层质量保障 |
| 偏好系统 | 仅任务级（[B] 用户补充） | 三层：任务/课程/用户 | 渐进实现，方向正确 |
| PDF 回退方案 | 无 | Post-processing 条件建议 | 防止反复试错 |

### 3.2 当前系统做得好的部分

以下部分不需要改：

1. **侦查阶段（Stage 1-5）工作扎实**
   - spec.md 130 行，覆盖元数据、源追踪、主 spec 判断、交付物、评分标准、技术要求
   - review_a.json 证据链完整（14 个数据源）
   - 识别了 LaTeX style file 缺失、数据集需外源获取等 gap

2. **工作台结构设计合理**
   - canvas/ / spec.md / investigation/ / references/ / draft/ 分层清晰
   - 只需在 skill Contract 中引用即可，不需要改结构

3. **用户检查点 [B] [E] 设计合理**
   - 两个 AskUserQuestion 足够，不过度打断

4. **state 追踪（result.json 四种状态）**
   - 简单有效，不需要改

---

## 4. 对新 Spec 开发的具体建议

### 4.1 必须优先解决：Skill 可发现性

新 spec §2 描述了 _index.md → 父级 skill → 子技能的三层发现，但**没有解决"agent 怎么找到 _index.md"这个问题**。

建议在 spec 中增加 §2.4 "路径发现规则"：

```markdown
## §2.4 路径发现规则

agent 的工作目录在 data/homework/<COURSE>/<HWID>/，skill 文件在仓库根下。
推导规则：
  - WORK_DIR = data/homework/<COURSE>/<HWID>/
  - REPO_ROOT = 从 WORK_DIR 向上 3 级目录
  - SKILLS_DIR = REPO_ROOT/sub-skills/tools/
  - _INDEX = SKILLS_DIR/_index.md

在 do-homework.md [A2] 创建工作台时，必须将 SKILLS_DIR 的绝对路径
写入 work_dir/.skills-path 文件，后续所有 skill 读取基于此路径。
```

### 4.2 pipeline_design.md 格式建议

新 spec §5 的 Stage 格式很好，建议增加：

- `fallback`：当首选工具不可用时的回退方案（防止 P3 的反复试错）
- `min_quality`：最低质量门槛（如 PDF > 10KB, 页数 >= 5）

### 4.3 Self-check 清单建议

新 spec §8.2 的自检很好，建议对 code-writer 特别增加：

```markdown
## Self-check (code-writer)
- [ ] 代码能在干净环境中运行无报错
- [ ] notebook 实际执行过，输出 cell 非空
- [ ] 报告中的数据指标来自实际运行结果，不是预估值
- [ ] 没有 [TODO] / [PROBLEM N] 占位符
```

### 4.4 Post-processing 回退链建议

新 spec §4.1 的 Post-processing 机制很好，建议对 pdf-renderer 明确写出回退链：

```markdown
## Post-processing (pdf-renderer)
- 如果 tectonic 可用 → tectonic 两步路径
- 如果 tectonic 不可用但 pandoc + xelatex 可用 → pandoc 路径
- 如果都不可用 → fpdf2 纯 Python 路径 + human_review_items 标注"排版质量降级"
```

### 4.5 子代理执行环境注意事项

基于 P5 的发现，新 spec 的 skill 文件中应考虑：

- Write 工具在子代理沙箱中可能被限制
- 建议在 skill 的 Invocation 部分提供 Bash heredoc 替代方案
- 或建议不在沙箱中执行 pipeline（在主 agent 中执行）

---

## 5. 附录：子代理工具调用完整时间线

| # | 工具 | 目标 | 结果 |
|---|------|------|------|
| 1 | Bash | ls project/ 目录 | ✅ canvas/ + references/ |
| 2 | Bash | ls canvas/ 目录 | ✅ 16 个 JSON |
| 3 | Bash | ls references/ 目录 | ✅ 7 个文件 |
| 4 | Bash | ls sub-skills/ 目录 | ❌ 不存在 |
| 5-19 | Read | canvas/*.json + references/*.txt (15 files) | ✅ 全部成功 |
| 20 | Bash | mkdir -p investigation draft workbench | ✅ |
| 21 | Write | spec.md | ✅ |
| 22 | Write | investigation/rubric.md | ✅ |
| 23 | Write | investigation/unreachable.txt | ✅ |
| 24 | Write | investigation/review_a.json | ✅ |
| 25 | Write | investigation/user_notes.md | ✅ |
| 26 | Write | pipeline_design.md | ✅ |
| 27 | Bash | python3 --version && pip3 list | ✅ |
| 28 | Bash | which tectonic/pandoc/wkhtmltopdf | tectonic ✗ pandoc ✓ wkhtmltopdf ✗ |
| 29 | Bash | pip3 install numpy pandas matplotlib sklearn seaborn nbformat | ✅ |
| 30-31 | Bash | 下载+解压 Student Dropout 数据集 | ✅ 533KB |
| 32 | Bash | python3 探索数据集 | ✅ 4424 samples, 37 features |
| 33 | Write | workbench/build_notebook.py | ✅ |
| 34 | Bash | python3 build_notebook.py | ❌ 嵌套三引号 SyntaxError |
| 35 | Read | build_notebook.py (定位 bug) | ✅ |
| 36 | Edit | 修复 docstring | ✅ |
| 37 | Bash | python3 build_notebook.py (retry) | ❌ 另一处嵌套三引号 |
| 38 | Write | workbench/build_notebook_v2.py (重写) | ✅ |
| 39 | Bash | python3 build_notebook_v2.py | ✅ 45 cells |
| 40-41 | Bash | cp data.csv + 验证 notebook | ✅ |
| 42 | Write | draft/report_G01_dropout.md | ❌ 沙箱限制 |
| 43 | Bash | cat > report.md (heredoc) | ✅ |
| 44 | Bash | pandoc → PDF | ❌ 缺 xelatex |
| 45 | Bash | pandoc → HTML | ✅ |
| 46 | Bash | pip3 install weasyprint | ✅ |
| 47 | Bash | weasyprint HTML → PDF | ❌ 缺系统库 |
| 48 | Bash | pip3 install fpdf2 | ✅ |
| 49 | Bash | gen_report_pdf.py (fpdf2) | ❌ Unicode 编码 |
| 50 | Bash | sed 修复 bullet 字符 | 部分修复 |
| 51 | Bash | gen_report_v3.py (fpdf2 简化) | ✅ 5 页 PDF |
| 52 | Bash | gen_presentation.py (fpdf2) | ✅ 11 页 PDF |
| 53 | Bash | pip3 freeze → requirements.txt | ✅ |
| 54 | Bash | zip 打包 | ✅ |
| 55-56 | Bash | 验证 draft + zip 内容 | ✅ |
