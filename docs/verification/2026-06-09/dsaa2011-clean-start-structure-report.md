# DSAA2011 Clean-Start Unified-Flow 验证报告

日期：2026-06-09

工作台：`data/homework/DSAA2011/project`

运行期协调者 B：`019eaba1-7960-71a0-9518-953b2df695fc`

轨迹审查者 D：`019eabda-3c47-7970-8c63-e12251e6fe43`

## 执行摘要

这次验证从一个干净启动状态运行当前统一版 `do-homework` 流程，目标是
DSAA2011 Project。active workbench 启动时只有 `archive/` 和
`prelaunch_startup_inventory.json`；作业事实、计划文件、草稿产物、审查
receipt、验证日志和 transcript 证据都在本轮重新生成。

产物侧结果较强：B 生成了本地 `draft_ready` 状态的 DSAA2011 Student
Dropout 项目包，并且没有提交 Canvas。包内包含 notebook、report PDF、
presentation PDF、requirements 文件和数据 CSV。本轮使用真实代码执行、
UCI Student Dropout 数据集、三轮实验迭代记录、实测 metrics，以及 13 张
生成图表。

流程侧结论是 `PASS_WITH_CONCERNS`，不是干净 `PASS`。D/E 轨迹审查确认
所有可用 runtime child transcript 都被审查，包括 alignment 前的 explore
scout。剩余问题集中在流程硬化：transcript 由 A fallback 导出、一个被
supersede 的 child 读取了禁止的 development/progress context、child receipt
依赖 ledger-authority identity 而不是 child-known id、若干非任务影响的
startup/plugin 噪音，以及少量 receipt/timestamp/schema 弱点。

## 本轮验证了什么

### Clean-Start 启动边界

accepted startup inventory 声明：

- `entry_preset: clean_start`
- `declared_mode: full_flow`
- 无 retained startup files
- 无 allowlisted history files
- `archive/`、旧 transcripts、旧 reviews/results、旧 verification logs、旧
  `result.json`、prior diagnostics、development validation docs 均为 forbidden
  context

这给了 B 一个真正干净的 runtime surface。旧 DSAA 证据只保留在 `archive/`
中，作为禁止读取的 rollback evidence。

### 模拟用户 Alignment

本轮在启动时显式提供了用户拥有的方向性决策：

- dataset：Student Dropout
- group id 占位：`G01`
- 只生成本地草稿，不提交 Canvas
- 必须真实运行代码和实验
- 报告要丰富，并且基于实际实验结果
- 必须有多轮 measured tuning，并根据结果调整实验

B 仍然写入了 `investigation/user_notes.md` 和
`investigation/alignment_brief.md`。它没有继续询问真人问题，因为这些
simulated supplements 已经覆盖会改变方向的关键选择。

### Alignment 前 Explore Scout

B 在 alignment 前 dispatch 了一个 read-only `source_spec` explore scout：

- agent id：`019eaba4-8f65-7ed1-8b09-db70e1ef5857`
- brief：`stage_briefs/explore_scout_source_spec.md`
- receipt：`investigation/scout_results/source_spec_result.json`
- ledger dispatch index：1

scout 确认了作业主规范来源：Canvas assignment page 为空，Canvas rubric
不存在；module `12955` 中的 `DSAA2011-26sp-project_announce-L01.pdf` 才是
governing spec。随后 B 重新生成了标准侦查产物：

- `canvas/`
- `references/DSAA2011-26sp-project_announce-L01.pdf`
- `references/DSAA2011-26sp-project_announce-L01.txt`
- `spec.md`
- `problem.md`
- `investigation/rubric.md`
- `investigation/unreachable.txt`
- `investigation/review_a.json`
- `investigation/explore_context.md`
- `investigation/explore_manifest.json`

artifact、codebase、history、verification scouts 都在 `explore_manifest.json`
中被记录为 `SKIPPED`，并写明 clean-start 原因。

## Runtime 结构

本轮生成了预期的 workbench 层次：

```text
prelaunch_startup_inventory.json
canvas/
references/
spec.md
problem.md
investigation/
  explore_context.md
  explore_manifest.json
  scout_results/source_spec_result.json
  rubric.md
  review_a.json
  user_notes.md
  alignment_brief.md
pipeline_design.md
stage_briefs/
stage_results/
stage_reviews/
transcripts/
draft/
verification_checklist.md
verification.log
result.json
coordinator_summary_cleanstart_20260609.md
```

execution plan 分为三个阶段：

1. `stage_01_experiments`
   - delegated executor
   - spec review
   - quality review
   - 产出数据集、脚本、notebook、metrics、iteration log、figures 和
     requirements

2. `stage_02_deliverables`
   - delegated executor
   - spec review
   - quality review
   - 产出 report PDF、presentation PDF、package directory 和 zip
   - 触发了 child replacement 和 repair/re-review loop

3. `stage_03_final_verification`
   - main-agent/coordinator verification
   - 产出 measured verification logs、`result.json` 和 coordinator summary

## Child Dispatch 时间线

coordinator ledger 中有 11 条 dispatch row 和 1 条 process event。

| Dispatch | Stage | Role | Status | Child Status |
|---:|---|---|---|---|
| 1 | explore_source_spec | explore_scout | accepted | DONE_WITH_CONCERNS |
| 2 | stage_01_experiments | executor | accepted | DONE_WITH_CONCERNS |
| 3 | stage_01_experiments | spec_reviewer | accepted | PASS |
| 4 | stage_01_experiments | quality_reviewer | accepted | PASS |
| 5 | stage_02_deliverables | executor | superseded_process_violation | DONE_WITH_CONCERNS |
| 6 | stage_02_deliverables | executor | accepted | DONE_WITH_CONCERNS |
| 7 | stage_02_deliverables | spec_reviewer | accepted | PASS |
| 8 | stage_02_deliverables | quality_reviewer | accepted | FAIL |
| 9 | stage_02_deliverables | executor_repair | accepted | DONE_WITH_CONCERNS |
| 10 | stage_02_deliverables | spec_reviewer_after_repair | accepted | PASS |
| 11 | stage_02_deliverables | quality_reviewer_after_repair | accepted | PASS |

这里最重要的结构行为是：B 没有隐藏坏路径。

- Dispatch 5 在检测到 forbidden development/progress reads 后被保留并
  supersede。
- Dispatch 8 的 quality failure 被保存在
  `stage_02_deliverables_quality_review_failed_before_repair.json`。
- Dispatch 9-11 形成了 bounded repair 和 after-repair re-review 路径。

## 产物结果

最终 `result.json` 状态：`draft_ready`

Canvas submission：`false`

主要产物：

- `draft/G01_student_dropout.zip`
- `draft/report_G01_student_dropout.pdf`
- `draft/presentation_G01_student_dropout.pdf`
- `draft/project_G01_student_dropout.ipynb`
- `draft/requirements_G01_student_dropout.txt`
- `draft/data/student_dropout.csv`

实测 artifact checks：

- `verification.log`：28 PASS / 3 SKIP
- notebook error outputs：0
- report PDF：7 页
- presentation PDF：11 页
- generated figures：13 个 PNG
- dataset：4,424 行，37 列
- zip integrity：通过
- no Canvas submission：通过

报告内容基于真实 metrics，包括模型比较、F1、ROC/AUC 讨论，以及三轮 tuning
narrative。

## Transcript 与 D/E 审查结构

A 通过 exact local-session agent-id match 导出了 9 个 runtime transcripts：

- coordinator B transcript：783 行
- 8 个唯一 runtime child transcripts
- `missing_count: 0`

部分 repair/re-review dispatch 复用了同一个 child agent id，因此映射到同一个
transcript body。`transcript_inventory.json` 记录了这个映射关系。

D 随后 dispatch 了 8 个 E transcript auditors，每个唯一 runtime child
transcript 一个。E audit verdict 分布为：

- PASS：1
- PASS_WITH_CONCERNS：6
- FAIL：1

唯一的 FAIL 属于被 supersede 的 Stage 2 executor。它不计入 accepted final
path evidence；相反，它支持 B 的 supersession decision。accepted-path child
verdict 分布是 PASS 1 / PASS_WITH_CONCERNS 6 / FAIL 0。

D 的最终 verdict 是 `PASS_WITH_CONCERNS`。

## 发现的问题

### 1. Direct Parent Transcript Export 仍然缺失

B 无法直接导出 child transcripts。B 完成后，A 通过精确匹配本地
`.codex/sessions` JSONL 文件恢复了完整 transcript evidence。这保证了 audit
coverage，但它仍然是 fallback evidence，不是理想的 direct-parent export。

影响：阻止 clean `PASS`，但不影响本轮验证成立。

可能的硬化方向：改进 direct parent export 能力，或者在需要 clean
transcript-body PASS 时使用 inspectable thread harness。

### 2. 一个 Stage 2 Executor 读取了 Forbidden Context

第一个 Stage 2 executor 在读取 stage brief 前，先读取了外部
workflow/development-plane context，包括 progress/backlog 文件。B 正确地将
该 dispatch 标记为 `superseded_process_violation` 并派出 replacement。

影响：最终 artifact path 由 replacement executor 支撑，但本轮不能算 clean，
因为确实有一个 child 偏离了 curated runtime context。

可能的硬化方向：child startup prompt 需要更强地约束“只读 brief”；如果平台
允许，还应阻止 runtime child 继承 development-plane startup habits。

### 3. Child Identity 可审，但不是最干净的写入时身份

多数 child receipts 使用：

```json
"agent_id": null,
"agent_id_source": "unknown_to_child_at_write_time",
"identity_authority": "stage_reviews/child_dispatch_ledger.json"
```

这是协议允许的 fallback，B 的 ledger 也保存了 authoritative agent ids。
但是更干净的证据应当是：每个 child 在自己的 receipt 中写入 exact runtime
id。

影响：identity 支持 `PASS_WITH_CONCERNS`，但不是 clean `PASS` 的理想状态。

可能的硬化方向：spawn 后、任务执行前注入 exact child id，然后强制 child
receipt 写入该 exact id。

### 4. 多个 Child Transcript 中出现 Startup/Plugin Scope 噪音

若干 child transcript 包含 Superpowers startup skill 的读取。E auditors
多数将其分类为 non-influential platform startup noise，因为 child 随后立即
回到 stage brief，并没有把该 skill 作为任务证据。

影响：这些 transcript 的 clean `PASS` 会被 cap，但不会让 accepted artifact
path 失败。

可能的硬化方向：继续区分 unavoidable startup noise 和主动使用外部 workflow
context；同时探索一种 runtime child launch mode，尽量完全抑制这些 startup
reads。

### 5. Receipt Timestamp 与 Repair Schema 需要收紧

replacement Stage 2 executor receipt 的 `created_at_utc` 早于 replacement
child transcript 的开始时间，说明它可能使用了 stage-level timestamp 或复制了
旧 attempt 的时间。after-repair spec review 的顺序虽然可由 ledger timestamps
和 transcript evidence 支持，但 receipt 缺少专门的 repair-result dependency
字段。

影响：artifact evidence 仍然成立，但 timestamp/order proof 不够干净。

可能的硬化方向：增加明确的 repair/re-review receipt 字段，例如
`depends_on_failed_review`、`depends_on_repair_result`、
`repair_attempt_index`、`supersedes_receipt_path`；并要求 child 在写 receipt
时捕获 child-local timestamp。

### 6. Runtime 工作泄漏到了 Repo 级 Docs/Tool Contracts

D/E 审查后，Main Agent A 发现 workbench 外存在新的 tracked diffs：

- `docs/PITFALLS.md`
- `sub-skills/tools/pdf-renderer.md`

这些修改记录了本轮一个真实的 PDF 渲染经验：`pdfimages` 可以证明图片已嵌入，
但不能证明图片没有被 page boundary 裁切或漂移，尤其在 TeX log 出现
figure-related `Overfull \vbox` warnings 时。内容本身有价值，经过 review 后
可能确实应该进入仓库。流程上，它仍然是 scope leak：runtime homework
children 理应只写 workbench artifacts，而不应在 homework run 中直接修改
AutoStudy development docs 或 tool contracts。

影响：这是 D receipt 之外额外发现的 process concern。它不影响 DSAA
deliverables，但说明 trajectory review 还不够：Main Agent A 还必须在验证后
检查 repo diff，并分类所有 out-of-workbench writes。

可能的硬化方向：

1. Stage briefs 明确禁止编辑 repo-level docs 和 skill/tool files，除非当前
   stage 本身就是 development-doc stage。
2. B final verification 应运行 `git status --short`，并报告所有非预期 tracked
   repo diffs。
3. D trajectory checklist 应加入 out-of-workbench write audit，而不只审
   child transcript 和 workbench receipts。
4. runtime 中发现的有价值经验应作为 proposed follow-up changes 报告出来，
   由 Main Agent A 在 development plane 应用，而不是由 runtime child 直接写入。

## 结构性结论

统一流程的整体形状是成立的。本轮不仅跑了 happy path，还实际覆盖了：

- clean startup inventory
- pre-alignment explore scout
- 标准 recon artifact generation
- simulated alignment bridge
- stage-based pipeline design
- executor/spec-review/quality-review loop
- child process violation 后 replacement
- quality failure preservation
- bounded repair
- after-repair re-review
- final verification
- transcript inventory
- D/E transcript-body audit

最强的结果不是“DSAA 产物做出来了”，而是流程暴露并保留了自己的缺陷。系统没有
静默接受坏 child，没有隐藏 failed quality review，没有跳过 scout audit，也没有让
D 用总评替代 E 的逐 transcript 审查。

下一轮应优先做 clean-PASS hardening，而不是继续打磨作业质量：

1. child id injection before task execution；
2. direct parent transcript export 或 inspectable thread harness；
3. 更严格隔离 child startup 与 development-plane docs；
4. repair/re-review receipt schema 增加显式 dependency fields；
5. child-local receipt timestamp discipline；
6. replacement receipt 覆盖标准文件前，先把 superseded receipts 保存到稳定路径；
7. post-run repo diff audit，检查 homework workbench 外的非预期写入。

## 最终判断

Artifact verdict：PASS。

Process verdict：PASS_WITH_CONCERNS。

本轮作为 unified flow 的 developer validation 是成功的：它证明了主架构可运行，
也暴露了具体硬化项。但在 transcript export、child identity、startup isolation、
repair receipt schema 和 out-of-workbench write audit 收紧之前，不能算 clean
process PASS。
