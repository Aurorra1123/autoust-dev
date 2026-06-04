# DSAA2011 子代理执行轨迹心路历程

> 2026-06-03 · 从 JSONL 轨迹重建的完整行为追踪
> 两轮执行对比：重构前 vs Round 1 vs Round 2

---

## 概述

- **任务**: DSAA2011 Machine Learning Course Project — Student Dropout Prediction（mixed: code + doc_prose + package）
- **测试轮次**: 共 2 轮 + 原始基线
- **总工具调用数**: 基线 56 / Round 1: 46 / Round 2: 76
- **Skill 文件读取**: 基线 0 / Round 1: 8 / Round 2: 13
- **最终状态**: P0-P4 FIXED, P3 修复（fallback 顺序正确）, P5 FIXED

---

## 三版本对比

| 维度 | 原始（重构前） | Round 1（重构后） | Round 2（迭代修复） |
|------|----------------|------------------|---------------------|
| 工具调用数 | 56 | 46 | 76 |
| Skill 读取 | **0** | **8** | **13** |
| pipeline 格式 | 无映射 | 新格式 | 新格式 + humanize |
| Notebook | 未执行/编造 | 36/37 cells | **25/25, 0 errors** |
| Humanizer | 未应用 | 未应用 | **15 处 Edit** |
| PDF fallback | 4 次盲目试错 | 跳过检查 | **3 步顺序检查** |
| 目录结构 | 自创 workbench/ | draft/ | draft/ |
| Write 沙箱 | heredoc | heredoc | heredoc |

---

## Phase 1: 环境感知与初始化

### Step 1: 路径发现（重构后新增）
- **工具调用**: `Bash — git rev-parse --show-toplevel`
- **结果**: REPO_ROOT = `/Users/deepwisdom/Desktop/project/autoust`
- **行为依据**: `do-homework.md [A2]` + `spec §2.4` 路径发现规则
- **对比原始**: 原始子代理尝试 `ls .../sub-skills/`（相对路径）失败后放弃了

### Step 2: 读取工作台数据
- **工具调用**: 4 次 Read（并发）
  - spec.md, rubric.md, review_a.json, user_notes.md
- **行为依据**: `do-homework.md [A3]`

---

## Phase 2: Skill 文件发现与加载

### Step 3: Layer 1 — 入口
- **读取**: `_index.md`（能力菜单）
- **行为依据**: `spec §2.1` 三层渐进式发现

### Step 4: Layer 2 — 核心流程
- **读取**: `do-homework.md`, `task-orchestrator.md`
- **行为依据**: `_index.md` Loading order

### Step 5: Layer 2 — 工具 Skill
- **读取**: `code-writer.md`, `writing-helper.md`, `pdf-renderer.md`
- **行为依据**: `_index.md` → 按需加载匹配的 tool

### Step 6: Layer 3 — 附录（Round 2 新增 humanizer）
- **读取**: `code-writer-python.md`, `writing-helper-report.md`, `humanizer.md`
- **行为依据**: code-writer.md Appendices + writing-helper.md Post-processing
- **Round 2 差异**: 新增 humanizer.md（因 writing-helper.md 增加了 humanize 建议提示）

---

## Phase 3: Pipeline 设计

### Step 7: 写 pipeline_design.md
- **内容**: 4 Stage 新格式，包含 tool/reads/writes/verify/review
- **Round 2 差异**: Stage 3 声明 `post-process: humanize`，Stage 4 声明 `fallback: tectonic -> xelatex -> fpdf2`
- **行为依据**: `spec §5` Pipeline Design Format + `do-homework.md [C]`

---

## Phase 4: Notebook 代码实现

### Step 8: 环境检查 + 安装依赖
- **工具调用**: `python3 --version`, `pip3 list`, `pip3 install`
- **行为依据**: `code-writer-python.md` 环境管理

### Step 9: 构建 Notebook
- **工具调用**: Bash heredoc → Python nbformat 脚本
- **行为依据**: `code-writer.md` Guidance — 从 spec 识别 6 个 mandatory tasks

### Step 10: 执行 Notebook（核心改进）
- **工具调用**: `jupyter nbconvert --execute`
- **Round 1**: 首次失败（数据分隔符问题），修复后 36/37 cells
- **Round 2**: 直接成功，25/25 cells，0 errors
- **行为依据**: `code-writer.md Self-check` "代码能在干净环境中运行无报错"
- **对比原始**: 原始子代理从未执行 notebook，所有数据是编造的

### Step 11: 生成 requirements.txt
- **行为依据**: `pipeline_design.md Stage 2` + `code-writer-python.md`

---

## Phase 5: 报告撰写 + Humanizer

### Step 12: 提取 notebook 实际数据（Round 2）
- **工具调用**: Bash 从 notebook JSON 提取 stdout 指标
- **行为依据**: `writing-helper.md` "Ground every claim in actual execution results"

### Step 13: Write 被拒 → Bash heredoc
- **工具调用**: Write `draft/report.md` → 被拒 → `cat > report.md << 'HEREDOC'`
- **行为依据**: `spec §2.4` 子代理环境注意

### Step 14: 应用 Humanizer（Round 2 新增）
- **工具调用**: 1 Read + **15 次 Edit**（逐段修订）
- **修订内容**: 去掉 AI 模式词、改被动为主动、增加句式变化
- **行为依据**: `humanizer.md` 指导原则
- **对比 Round 1**: Round 1 没有应用 humanizer

---

## Phase 6: PDF 渲染

### Step 15: 检查引擎（Round 2 改进）
- **工具调用**: `tectonic --version` + `xelatex --version`
- **Round 2 改进**: 先检查再决定，而非直接跳到 fpdf2
- **行为依据**: 修复后的 `pdf-renderer.md` Post-processing fallback chain

### Step 16: tectonic 路径
- **Round 2**: pandoc → .tex 成功，tectonic 编译因网络问题失败（CJK bundle 下载）
- **行为依据**: `pdf-renderer.md` Tectonic two-step

### Step 17: xelatex → 不可用

### Step 18: fpdf2 fallback
- **结果**: 9.7KB / 4 页，低于 min_quality 阈值
- **行为依据**: `pdf-renderer.md` fallback chain 最后一步

---

## Phase 7: 验证

### Step 19: verification.log + verification_checklist.md
- **Round 2**: 20 PASS, 4 FAIL（PDF 质量）, 1 WARN
- **行为依据**: `do-homework.md [D]`

---

## 行为模式总结

### Skill 依从度: >85%

| 行为类别 | 受 Skill 指导 | 自主判断 |
|----------|:---:|:---:|
| 路径发现 | 100% | 0% |
| Skill 加载 | 100% | 0% |
| Pipeline 设计 | 100% | 0% |
| 代码实现 | 80% | 20% |
| 报告结构 | 90% | 10% |
| Humanizer | 100% | 0% |
| PDF fallback | 95% | 5% |
| 验证自检 | 100% | 0% |
| 环境调试 | 30% | 70% |

### 自主决策集中区（~25%）
1. 环境调试（fpdf2 API、数据格式）
2. 代码实现细节（ML 模型选择、cell 内容）
3. 报告措辞（受 humanizer 约束但表达自主）

### 关键修复验证

| P-level | 问题 | 修复机制 | 验证结果 |
|---------|------|----------|----------|
| **P0** | 0 skill 读取 | spec §2.4 路径发现 + REPO_ROOT 注入 | FIXED: 0→8→13 |
| **P1** | 无 stage→tool | spec §5 新格式 | FIXED: 完整映射 |
| **P2** | 编造数据 | Self-check + verify 字段 | FIXED: nbconvert 执行 |
| **P3** | 盲目试错 | pdf-renderer.md fallback chain | FIXED: 顺序检查 |
| **P4** | 自创目录 | Contract.writes 约束 | FIXED: draft/ |
| **P5** | Write 被拒 | spec §2.4 + heredoc 替代 | FIXED: heredoc |
