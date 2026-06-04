# Pipeline 执行轨迹审计报告 — UCUG1505

> 2026-06-03 · UCUG1505 Creative Coding Final Project 实测记录
> 测试方式：派独立子代理从 canvas/ 原始数据开始，走完整侦查→设计→执行流程
> 对比基准：DSAA2011 同期两轮验证结果

---

## 1. 测试概述

### 1.1 测试方法

- **测试对象**：AutoStudy do-homework 完整流程（侦查 [A] → 设计 [C] → 执行 [D]）
- **测试手段**：派独立子代理执行，派另一个子代理分析 JSONL 轨迹
- **测试用例**：UCUG1505 Creative Coding Final Project（mixed 类型：code 80% + doc_prose 5% + video_manual 15%）
- **模拟用户输入**：项目概念、技术栈、组员名（绕过 human blockers）
- **与 DSAA2011 的关键区别**：workbench 只保留 canvas/ 原始数据，子代理从零开始

### 1.2 测试环境

- 工作目录：`data/homework/UCUG1505/final-project/`
- canvas/ 原始数据：16 个 JSON 快照
- tectonic：v0.16.9（CJK bundle 已缓存）
- pandoc：v3.9.0.2
- 子代理工具调用：63 次（Read 22, Bash 12, TaskUpdate 12, Write 11, TaskCreate 5）

### 1.3 总体结果

**P0-P5 全部 FIXED，首轮通过，无需迭代。**

| 维度 | DSAA2011 Round 0 | DSAA2011 Round 2 | UCUG1505 |
|------|------------------|------------------|----------|
| P0 Skill 读取 | 0 | 13 | **7** |
| P1 Stage→Tool | 无映射 | 完整 | **完整** |
| P2 代码真实性 | 编造 | 25/25 cells | **340 行真实代码** |
| P3 PDF 回退 | 4 次试错 | 3 步检查 | **tectonic 两步成功** |
| P4 目录结构 | 自创 workbench/ | draft/ | **draft/** |
| P5 Write 沙箱 | heredoc | heredoc | **Write 全部成功** |

---

## 2. P0: Skill 文件读取 — FIXED

子代理在执行之初按序读取了 7 个 skill 文件：

| 序号 | 文件 | 类型 |
|---|---|---|
| 1 | `sub-skills/tools/_index.md` | 必读（Layer 1） |
| 2 | `sub-skills/tasks/do-homework.md` | 必读（流程指导） |
| 3 | `sub-skills/tasks/task-orchestrator.md` | 必读（编排器） |
| 4 | `sub-skills/tools/code-writer.md` | 按需（Layer 2） |
| 5 | `sub-skills/tools/writing-helper.md` | 按需（Layer 2） |
| 6 | `sub-skills/tools/pdf-renderer.md` | 按需（Layer 2） |
| 7 | `sub-skills/tools/humanizer.md` | 按需（Layer 3） |

加载顺序完全符合 spec §2.1 三层渐进式发现。

---

## 3. P1: Stage→Tool 映射 — FIXED

pipeline_design.md 声明 4 个 Stage，每个有 tool/reads/writes/verify：

| Stage | 声明 tool | 实际执行 | 一致性 |
|---|---|---|---|
| Stage 1: Creative Code | code-writer | Write 写入 sketch.js/index.html/style.css | ✅ |
| Stage 2: Documentation | writing-helper | Write 写入 documentation.md | ✅ |
| Stage 3: PDF Rendering | pdf-renderer | pandoc+tectonic 两步渲染 | ✅ |
| Stage 4: Zip Packaging | inline (shell) | `zip -r project-code.zip` | ✅ |

---

## 4. P2: 代码真实性 — FIXED

- sketch.js: 340 行，9839 bytes，完整 Particle 类
- 4 种行为模式：scatter, spiral, wave, constellation
- Web Audio API 麦克风输入 + FFT 分析
- 600 粒子系统，Perlin 噪声叠加
- 无 TODO/FIXME/placeholder

---

## 5. P3: PDF 回退链 — FIXED

执行序列：
1. `tectonic --version` → TECTONIC_OK (v0.16.9)
2. `pandoc --version` → pandoc 3.9.0.2
3. `pandoc documentation.md -o .tex` (markdown → LaTeX)
4. `tectonic .tex --outdir draft/` (LaTeX → PDF)
5. `head -c 4` 验证 `%PDF` magic bytes

最终 PDF: 28,172 bytes，大于 min_quality 10KB。走的是最优路径（tectonic 可用），无需降级到 fpdf2。

---

## 6. P4: 目录结构 — FIXED

```
final-project/
├── spec.md                     (3890 bytes)
├── problem.md                  (1060 bytes)
├── pipeline_design.md          (2271 bytes)
├── verification.log            (1268 bytes)
├── investigation/
│   ├── rubric.md               (2000 bytes)
│   ├── review_a.json           (1613 bytes)
│   └── unreachable.txt         (525 bytes)
├── references/                 (空)
└── draft/
    ├── documentation.md        (3234 bytes)
    ├── documentation.pdf       (28172 bytes)
    ├── project-code.zip        (4591 bytes)
    └── project-code/
        ├── index.html          (706 bytes)
        ├── sketch.js           (9839 bytes)
        └── style.css           (926 bytes)
```

---

## 7. P5: 文件写入方式 — FIXED

- Write 工具: 11 次（全部成功）
- Bash heredoc: 0 次
- 说明：Write 工具在此环境未被沙箱拦截，与 DSAA2011 环境不同

---

## 8. 验证日志

```
PASS | project-code/index.html exists | measured: 706 bytes
PASS | project-code/sketch.js exists | measured: 9839 bytes
PASS | project-code/style.css exists | measured: 926 bytes
PASS | documentation.md exists | measured: 3234 bytes
PASS | documentation.pdf exists and has %PDF magic | measured: 28172 bytes
PASS | documentation.pdf > 10KB | measured: 28172 bytes
PASS | project-code.zip exists and is valid zip | measured: 4591 bytes
PASS | project-code.zip contains all 3 code files | measured: 4 entries
PASS | documentation word count <= 500 | measured: 418 words
PASS | documentation contains all required sections | measured: 7 sections
SKIP | video demo (2-3 min on YouTube/Vimeo) | reason: human_review
SKIP | video link in documentation | reason: human_review
SKIP | code runs without browser console errors | reason: human_review
SKIP | both partners submit same materials | reason: human_review
SKIP | documentation template exact sections match | reason: human_review
```
