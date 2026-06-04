# sync-course + write-course-notes 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现两个固定流水线 skill——sync-course（课程资料持久化同步）和 write-course-notes（并行 Agent 生成 Obsidian 风格课程笔记），用 DSAA2011 课程端到端验收。

**Architecture:** 两个独立 task skill，参考 AutoPku write-notes 的固定流水线 + 并行 Agent 模式。sync-course 负责增量下载课程资料到 `data/courses/<COURSE>/`，write-course-notes 消费课件 PDF 生成结构化笔记。不修改现有 do-homework 流程。

**Tech Stack:** Markdown skill files, canvascli CLI, Claude Code Agent(), PyMuPDF (pdf-reader)

**Spec:** `docs/superpowers/specs/2026-06-04-sync-course-and-write-notes-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `sub-skills/tasks/sync-course.md` | 课程级资料持久化同步 skill |
| Create | `sub-skills/tasks/write-course-notes.md` | 课程笔记生成 skill（固定流水线 + 并行 Agent） |
| Modify | `sub-skills/tools/_index.md` | 注册两个新 task |
| Modify | `skill.md` | 添加两个新 task 的路由规则 |

---

### Task 1: Create sync-course.md

**Files:**
- Create: `sub-skills/tasks/sync-course.md`

- [ ] **Step 1: Create sync-course.md with YAML frontmatter and preconditions**

Write the file `sub-skills/tasks/sync-course.md` with the following content:

```markdown
---
name: sync-course
description: Sync course materials (lectures, readings, announcements) to persistent per-course storage. Use when the user asks to download course files, sync course materials, or prepare for note-taking.
---

# Sync Course

Persistent course-level material sync. Downloads and organizes Canvas files,
announcements, and module structure into `data/courses/<COURSE>/`.

Unlike `sync-status` (which builds a homework plan), this skill builds a
**course archive** — a reusable data store that feeds `write-course-notes` and
future learning tools.

## Preconditions

Before running, check:
1. `.venv/` exists with `canvascli` installed (test: `.venv/bin/canvascli --version`)
2. A saved session exists (test: `.venv/bin/canvascli whoami` returns 0)

If either is missing, redirect to `canvascli-setup.md`. Do NOT proceed silently.

## Trigger patterns

| User says... | Mode |
|---|---|
| "同步 DSAA2043 的资料" / "下载 XX 课的课件" / "sync course materials for X" | Single course |
| "同步所有课程资料" / "下载全部课件" / "sync all course materials" | Batch (all active-term courses) |

## Execution flow

### Step 1: Discover courses

```bash
.venv/bin/canvascli courses 2>/dev/null > data/courses.json
```

**Single-course mode**: Ask the user to confirm the course name (match from
`data/courses.json`). Extract `course_id`.

**Batch mode**: List all courses from the JSON. Use `AskUserQuestion` to let the
user confirm which courses to sync (multi-select or "all").

### Step 2: Sync one course (repeat per course in batch)

For each selected course, run steps 2a–2h.

#### 2a. Create directory structure

```bash
COURSE_DIR="data/courses/<COURSE_SLUG>"
mkdir -p "$COURSE_DIR"/{materials/{lectures,readings,other},canvas_sync,notes}
```

`<COURSE_SLUG>` is `course_code` uppercased and non-alphanumeric replaced with
`-` (e.g. `DSAA2011`). If `course_code` is empty, derive from the course name.

#### 2b. Write meta.json

```bash
.venv/bin/python -c "
import json, datetime
course = json.load(open('data/courses.json'))
target = [c for c in (course if isinstance(course, list) else [course]) if str(c['id']) == '$COURSE_ID'][0]
slug = (target.get('course_code') or target['name'].split(' - ')[0]).strip().upper()
slug = ''.join(c if c.isalnum() else '-' for c in slug).strip('-')
meta = {
    'course_id': str(target['id']),
    'name': target['name'],
    'course_code': target.get('course_code', ''),
    'term': target.get('term', ''),
    'slug': slug,
    'synced_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
    'file_counts': {}
}
import pathlib; pathlib.Path('$COURSE_DIR/meta.json').parent.mkdir(parents=True, exist_ok=True)
json.dump(meta, open('$COURSE_DIR/meta.json', 'w'), ensure_ascii=False, indent=2)
print(f'meta.json written for {slug}')
"
```

#### 2c. Fetch file listing

```bash
.venv/bin/canvascli files --course-id <CID> > "$COURSE_DIR/canvas_sync/files_index_new.json"
```

#### 2d. Incremental diff

Compare `files_index_new.json` against the existing `canvas_sync/files_index.json`
(if any). Extract files that are new or have a different `updated_at`.

```bash
.venv/bin/python -c "
import json
new = json.load(open('$COURSE_DIR/canvas_sync/files_index_new.json'))
try:
    old = {f['id']: f for f in json.load(open('$COURSE_DIR/canvas_sync/files_index.json'))}
except (FileNotFoundError, json.JSONDecodeError):
    old = {}
to_download = []
for f in (new if isinstance(new, list) else new.get('files', [])):
    fid = f.get('id')
    if fid not in old or old[fid].get('updated_at') != f.get('updated_at'):
        to_download.append(f)
print(f'New: {len(to_download)}, Existing: {len(new) - len(to_download)}')
json.dump(to_download, open('/tmp/sync_course_to_download.json', 'w'), ensure_ascii=False, indent=2)
"
```

#### 2e. Classify and download

For each file to download, classify by filename/folder path:

```python
import re

def classify(filename, folder):
    name = (filename or '').lower()
    path = (folder or '').lower()
    patterns_lecture = r'lecture|lec|\.l\d|课件|slide|week\s*\d'
    patterns_reading = r'reading|paper|article|论文|ref|bib'
    if re.search(patterns_lecture, name + ' ' + path):
        return 'lectures'
    if re.search(patterns_reading, name + ' ' + path):
        return 'readings'
    return 'other'
```

Download each file:

```bash
.venv/bin/canvascli download <FILE_ID> -o "$COURSE_DIR/materials/<CATEGORY>/<FILENAME>"
```

#### 2f. Archive announcements

```bash
.venv/bin/canvascli announcements 2>/dev/null > /tmp/all_announcements.json
.venv/bin/python -c "
import json
all_ann = json.load(open('/tmp/all_announcements.json'))
course_ann = [a for a in (all_ann if isinstance(all_ann, list) else [])
              if str(a.get('course_id')) == '$COURSE_ID']
ann_path = '$COURSE_DIR/canvas_sync/announcements.json'
try:
    existing = json.load(open(ann_path))
    existing_ids = {a.get('id') for a in existing}
except (FileNotFoundError, json.JSONDecodeError):
    existing = []
    existing_ids = set()
merged = existing + [a for a in course_ann if a.get('id') not in existing_ids]
json.dump(merged, open(ann_path, 'w'), ensure_ascii=False, indent=2)
print(f'Announcements: {len(course_ann)} new, {len(merged)} total')
"
```

#### 2g. Fetch module structure

```bash
.venv/bin/canvascli modules --course-id <CID> > "$COURSE_DIR/canvas_sync/modules.json" 2>/dev/null || echo '[]' > "$COURSE_DIR/canvas_sync/modules.json"
```

#### 2h. Update files_index and generate index.md

```bash
cp "$COURSE_DIR/canvas_sync/files_index_new.json" "$COURSE_DIR/canvas_sync/files_index.json"
```

Then generate `$COURSE_DIR/index.md`:

```bash
.venv/bin/python -c "
import json, os
meta = json.load(open('$COURSE_DIR/meta.json'))
ann = json.load(open('$COURSE_DIR/canvas_sync/announcements.json'))
files = json.load(open('$COURSE_DIR/canvas_sync/files_index.json'))

# Count files by category
cats = {}
for f in (files if isinstance(files, list) else []):
    fname = f.get('display_name', f.get('filename', ''))
    folder = f.get('folder', '')
    # Use same classify logic
    import re
    name = fname.lower()
    path = folder.lower()
    if re.search(r'lecture|lec|\.l\d|课件|slide|week\s*\d', name + ' ' + path):
        cat = 'lectures'
    elif re.search(r'reading|paper|article|论文|ref|bib', name + ' ' + path):
        cat = 'readings'
    else:
        cat = 'other'
    cats.setdefault(cat, []).append(fname)

lines = [
    f'# {meta.get(\"course_code\", meta[\"name\"])} 课程总览',
    '',
    f'- **课程名**: {meta[\"name\"]}',
    f'- **学期**: {meta.get(\"term\", \"N/A\")}',
    f'- **上次同步**: {meta.get(\"synced_at\", \"N/A\")}',
    '',
    '## 资料清单',
    '',
]
for cat in ['lectures', 'readings', 'other']:
    items = cats.get(cat, [])
    lines.append(f'### {cat} ({len(items)} files)')
    for item in sorted(items):
        lines.append(f'- {item}')
    lines.append('')

if ann:
    lines.extend(['## 公告摘要', ''])
    for a in ann[:10]:
        lines.append(f'- **{a.get(\"title\", \"\")}** ({a.get(\"posted_at\", \"\")[:10]})')
    if len(ann) > 10:
        lines.append(f'- ... and {len(ann) - 10} more')
    lines.append('')

with open('$COURSE_DIR/index.md', 'w') as f:
    f.write('\n'.join(lines))
print('index.md generated')
"
```

Update `meta.json` with file counts:

```bash
.venv/bin/python -c "
import json, os, re
meta = json.load(open('$COURSE_DIR/meta.json'))
files = json.load(open('$COURSE_DIR/canvas_sync/files_index.json'))
cats = {}
for f in (files if isinstance(files, list) else []):
    fname = f.get('display_name', f.get('filename', '')).lower()
    folder = f.get('folder', '').lower()
    if re.search(r'lecture|lec|\.l\d|课件|slide|week\s*\d', fname + ' ' + folder):
        cat = 'lectures'
    elif re.search(r'reading|paper|article|论文|ref|bib', fname + ' ' + folder):
        cat = 'readings'
    else:
        cat = 'other'
    cats[cat] = cats.get(cat, 0) + 1
meta['file_counts'] = cats
json.dump(meta, open('$COURSE_DIR/meta.json', 'w'), ensure_ascii=False, indent=2)
"
```

### Step 3: Report results

Summarize per course:
- `<COURSE>: 新增 X 个文件, 跳过 Y 个已有文件, Z 个公告`
- Point user to `data/courses/<COURSE>/index.md` for the overview.

**Safety rules:**
- Do NOT auto-download without user confirmation of scope.
- Do NOT delete existing files. Only add new ones.
- Do NOT modify anything under `data/homework/`.
```

- [ ] **Step 2: Commit sync-course.md**

```bash
git add sub-skills/tasks/sync-course.md
git commit -m "feat: add sync-course task skill for course-level material archiving"
```

---

### Task 2: Create write-course-notes.md

**Files:**
- Create: `sub-skills/tasks/write-course-notes.md`

- [ ] **Step 1: Create write-course-notes.md with full fixed pipeline + Agent prompt template**

Write the file `sub-skills/tasks/write-course-notes.md` with the following content:

```markdown
---
name: write-course-notes
description: Generate structured course notes from lecture PDFs using parallel Agent Team. Fixed pipeline, Obsidian-style Markdown output with callouts and mermaid diagrams.
---

# Write Course Notes

Fixed-pipeline note generation from archived lecture PDFs. Uses a parallel
Agent Team — one Agent per lecture PDF — to produce structured, Obsidian-style
Markdown notes.

**Prerequisite**: `data/courses/<COURSE>/materials/lectures/` must contain PDFs
from a prior `sync-course` run. If empty, tell the user to run sync-course first.

**Reference**: Modeled after AutoPku's `write-notes` task skill.

## Execution flow (4 fixed steps)

### Step 1: Discover lectures

```bash
COURSE_DIR="data/courses/<COURSE>"
LECTURES_DIR="$COURSE_DIR/materials/lectures"

# List PDFs sorted by name
ls "$LECTURES_DIR"/*.pdf 2>/dev/null | sort || echo "NO_PDFS"
```

If `NO_PDFS`:
- Tell user: "这门课还没有同步课件资料。请先运行 sync-course 下载课件。"
- Stop.

If PDFs found, display the list with indices:
```
发现 X 个课件:
  1. L01-introduction.pdf (23 pages)
  2. L02-linear-algebra.pdf (31 pages)
  ...
```

### Step 2: User confirmation (AskUserQuestion — 3 questions)

```
AskUserQuestion({
    "questions": [
        {
            "question": "选择要撰写笔记的课件：",
            "options": [
                {"label": "全部课件", "value": "all"},
                {"label": "指定范围", "value": "range"}
            ],
            "multiSelect": false
        },
        {
            "question": "笔记详细程度：",
            "options": [
                {"label": "精简（只保留核心定义和定理）", "value": "minimal"},
                {"label": "标准（包含证明思路）", "value": "standard"},
                {"label": "详细（完整推导过程）", "value": "detailed"}
            ],
            "multiSelect": false
        },
        {
            "question": "额外要求（多选）：",
            "options": [
                {"label": "添加LaTeX公式编号", "value": "numbered_eq"},
                {"label": "添加概念之间的关联图", "value": "concept_map"},
                {"label": "添加例题（如有）", "value": "examples"}
            ],
            "multiSelect": true
        }
    ]
})
```

If "指定范围": ask which indices (e.g., "1, 3-5").

### Step 3: Parallel Agent Team — one Writer Agent per PDF

For each selected PDF, spawn a Writer Agent using Claude Code `Agent()`:

```python
agent_configs = []
for pdf_path in selected_pdfs:
    lecture_name = Path(pdf_path).stem  # e.g., "L01-introduction"
    agent_configs.append({
        "name": f"note-writer-{lecture_name}",
        "prompt": WRITER_AGENT_PROMPT.format(
            pdf_path=pdf_path,
            notes_dir=f"{COURSE_DIR}/notes",
            lecture_name=lecture_name,
            detail_level=detail_level,
            extra_options=extra_options
        ),
        "description": f"撰写 {lecture_name} 的课程笔记"
    })

# Spawn all agents in parallel (Claude Code Agent tool)
for config in agent_configs:
    Agent(name=config["name"], prompt=config["prompt"], description=config["description"])
```

**WRITER_AGENT_PROMPT** (fixed template, reference AutoPku write-notes):

```
你是笔记撰写专家，从课件中提取核心学术内容。

输入：{pdf_path}
输出：{notes_dir}/{lecture_name}.md
详细程度：{detail_level}
额外选项：{extra_options}

## 引用工具

使用 PyMuPDF (fitz) 读取 PDF：
```python
import fitz
doc = fitz.open("{pdf_path}")
text = "\\n\\n".join([page.get_text() for page in doc])
doc.close()
```

## 内容筛选原则（重要）

### ✅ 保留内容
- **Motivation**: 为什么要研究这个问题？核心问题是什么？
- **定义**: 形式化定义、符号表示
- **定理/命题**: 精确陈述，编号
- **证明**: 关键步骤、核心技巧
- **结论**: 主要结果、推论
- **技术工具**: 关键引理、构造方法

### ❌ 去除内容
- **历史背景**: 谁发明的、发展历程
- **故事/轶事**: 装饰性内容
- **重复性内容**: 多处出现的相同解释
- **装饰性语言**: "让我们来看看"、"有趣的是"等

### ❌ 写作反模式（严禁）
- **"不是X而是Y"句式**: 直接说Y是什么
- **过度分段**: 能用一段话讲清楚的不要拆成多段
- **废话填充**: 不要用过渡句、总结句、重复换词说同一件事

## 笔记格式（Obsidian 风格）

```markdown
# {Lecture 标题}

> [!tip] 学习指南
> 本节核心：{{一句话概括本节要解决什么问题}}
> 前置知识：{{需要哪些前面的概念}}
> 重点关注：{{考试/理解的关键点}}

## 核心问题/Motivation
- 本节要解决的中心问题
- 与前文的关系（如有）

## 定义

### 定义 X.X （概念名）
**陈述**: 形式化定义
**符号**: $...$

> [!note] 直觉理解
> {{用一两句话帮助建立直觉}}

## 定理与命题

### 定理 X.X （定理名）
**陈述**: 精确数学陈述
**证明**:
1. 关键步骤...
2. 核心技巧...

> [!warning] 易错点
> {{常见误解或易混淆之处}}

## 概念关系

用 mermaid 图展示本节概念之间的逻辑关系：
​```mermaid
graph TD
    A[概念A] --> B[概念B]
    B --> C[定理C]
​```

## 结论
- 本节主要结果总结
- 关键公式/事实

> [!tip] 复习要点
> {{本节最值得记住的1-3个结论}}

## 记号速查
| 符号 | 含义 |
|-----|------|
| $...$ | ... |
```

### Callout 使用规范

| Callout 类型 | 用途 | 示例场景 |
|-------------|------|---------|
| `> [!tip] 学习指南` | 每节开头，概括重点和前置知识 | 帮助预习定位 |
| `> [!note] 直觉理解` | 定义/定理旁，建立直觉 | "可以类比为……" |
| `> [!warning] 易错点` | 常见误解、易混淆概念 | "注意X和Y的区别" |
| `> [!tip] 复习要点` | 每节结尾，总结必记结论 | 快速回顾用 |
| `> [!example] 例题` | 典型例题（如用户选择了"添加例题"） | 巩固理解 |

### Mermaid 图使用规范

在以下场景必须使用 mermaid 图：
- 概念依赖关系：定义之间的推导链、定理之间的蕴含关系
- 证明结构：较长证明的步骤流程
- 分类讨论：情况分支（用 `graph TD` 或 `flowchart`）

## 约束
- 笔记必须是标准 Markdown（含 Obsidian callout 和 mermaid 语法）
- 数学公式使用 LaTeX（$...$ 行内，$$...$$ 行间）
- 保留原始课件的结构层次（章节编号）
- 如某节无数学内容（纯故事/历史），标注"本节为导言/背景，略"
- **写作风格**: 行文紧凑，禁用"不是X而是Y"句式，不堆砌过渡词
- **目标读者**: 预习或备考的大学生

返回：
- 处理页数
- 提取的定义数、定理数
- 输出文件路径
```

### Step 4: Generate index (README.md)

After all agents complete, generate `data/courses/<COURSE>/notes/README.md`:

```bash
.venv/bin/python -c "
import json, os
from pathlib import Path

course_dir = '$COURSE_DIR'
notes_dir = f'{course_dir}/notes'
meta = json.load(open(f'{course_dir}/meta.json'))

# Collect generated notes
notes = sorted(Path(notes_dir).glob('*.md'))
notes = [n for n in notes if n.name != 'README.md']

lines = [
    f'# {meta.get(\"course_code\", meta[\"name\"])} 课程笔记',
    '',
    f'生成时间：{meta.get(\"synced_at\", \"N/A\")}',
    f'课件数量：{len(notes)}',
    '',
    '## 笔记索引',
    '',
    '| # | 讲次 | 文件 |',
    '|---|------|------|',
]
for i, note in enumerate(notes, 1):
    lines.append(f'| {i} | {note.stem} | [{note.name}](./{note.name}) |')

lines.extend([
    '',
    '## 课程知识图谱',
    '',
    '```mermaid',
    'graph TD',
])

# Auto-generate concept links from note filenames
for i, note in enumerate(notes):
    if i > 0:
        lines.append(f'    L{i} --> L{i+1}')
    lines.append(f'    L{i+1}[{note.stem}]')

lines.extend([
    '```',
    '',
])

with open(f'{notes_dir}/README.md', 'w') as f:
    f.write('\n'.join(lines))
print(f'README.md generated with {len(notes)} notes indexed')
"
```

Report results:
- `X 个课件笔记已生成 → data/courses/<COURSE>/notes/`
- List each note file with page count and key topics extracted.

**Safety rules:**
- Do NOT overwrite existing notes without user confirmation.
- Do NOT modify anything under `data/homework/`.
- Do NOT generate PDF output — only Markdown.
```

- [ ] **Step 2: Commit write-course-notes.md**

```bash
git add sub-skills/tasks/write-course-notes.md
git commit -m "feat: add write-course-notes task skill with parallel Agent Team"
```

---

### Task 3: Register new skills in _index.md and skill.md

**Files:**
- Modify: `sub-skills/tools/_index.md`
- Modify: `skill.md`

- [ ] **Step 1: Add task registrations to _index.md**

In `sub-skills/tools/_index.md`, after the existing tool registry table, add a
new section for task skills (or append to the existing structure):

Add a **Task registry** section after the tool registry table:

```markdown
## Task registry

| Task | File | One-line capability | Trigger |
|---|---|---|---|
| **sync-course** | [../tasks/sync-course.md](../tasks/sync-course.md) | Persistent course material sync (files, announcements, modules) | "同步课程资料", "下载课件" |
| **write-course-notes** | [../tasks/write-course-notes.md](../tasks/write-course-notes.md) | Parallel Agent notes from lecture PDFs (Obsidian style) | "写笔记", "课程笔记" |
```

- [ ] **Step 2: Add routing rules to skill.md**

In `skill.md`, add two rows to the "What you can ask" table:

```markdown
| "同步 DSAA2011 的资料" / "下载课件" / "sync course materials" | → `sub-skills/tasks/sync-course.md` |
| "写 DSAA2043 的笔记" / "课程笔记" / "generate course notes" | → `sub-skills/tasks/write-course-notes.md` |
```

Also update the Architecture tree to include the new files:

```markdown
    ├── sync-status.md            ← M2 flagship task
    ├── sync-course.md            ← Course-level material archiving
    ├── task-orchestrator.md      ← M3 pipeline executor from pipeline_design.md
    ├── do-homework.md            ← MVP flagship: real Canvas assignment E2E
    └── write-course-notes.md     ← Parallel Agent course note generation
```

- [ ] **Step 3: Commit registration changes**

```bash
git add sub-skills/tools/_index.md skill.md
git commit -m "feat: register sync-course and write-course-notes in _index.md and skill.md"
```

---

### Task 4: End-to-end acceptance test with DSAA2011

**This is the critical validation task.** Run the full flow with real Canvas data
for the DSAA2011 course. If anything breaks or produces unsatisfactory output,
fix it and re-run until the output is clean and complete.

**No commit until the entire flow passes.**

- [ ] **Step 4a: Run sync-course for DSAA2011**

Simulate a user session:
1. Open a new Claude Code session in the autoust project directory
2. Say: "同步 DSAA2011 的资料"
3. Verify: the skill routes to sync-course correctly
4. Verify: `data/courses/DSAA2011/` directory is created with correct structure
5. Verify: `meta.json` is valid JSON with correct course info
6. Verify: `canvas_sync/files_index.json` contains file entries
7. Verify: `materials/lectures/` contains downloaded PDFs (if the course has any)
8. Verify: `canvas_sync/announcements.json` is valid JSON (may be empty)
9. Verify: `canvas_sync/modules.json` is valid JSON
10. Verify: `index.md` is human-readable and lists files by category

**If sync-course fails or produces wrong output:**
- Identify the failing step
- Fix the skill file
- Re-run from scratch (delete `data/courses/DSAA2011/` first)
- Repeat until clean

- [ ] **Step 4b: Verify sync-course output quality**

Check the following:
- [ ] `data/courses/DSAA2011/meta.json` — course_id, name, term all populated
- [ ] `data/courses/DSAA2011/canvas_sync/files_index.json` — has file entries with file_id, filename, updated_at, folder
- [ ] `data/courses/DSAA2011/materials/lectures/` — PDFs exist and are not zero-byte
- [ ] `data/courses/DSAA2011/index.md` — readable, files grouped by category
- [ ] No files under `data/homework/` were modified (independence check)

- [ ] **Step 4c: Run write-course-notes for DSAA2011**

Continue in the same session (or new session):
1. Say: "给 DSAA2011 写笔记"
2. Verify: the skill routes to write-course-notes correctly
3. Verify: AskUserQuestion appears with 3 questions (scope, detail, extras)
4. Select: "全部课件", "标准", "概念关联图"
5. Verify: Writer Agents are spawned (one per PDF in materials/lectures/)
6. Wait for all agents to complete
7. Verify: `data/courses/DSAA2011/notes/` contains one .md file per lecture PDF
8. Verify: `data/courses/DSAA2011/notes/README.md` index is generated

**If write-course-notes fails or produces poor notes:**
- Read the generated note files to assess quality
- Check for: correct callout syntax, mermaid blocks, LaTeX formulas, no placeholder text
- Identify issues (wrong prompt, missing PDF content, formatting errors)
- Fix the skill file
- Delete `data/courses/DSAA2011/notes/` contents
- Re-run
- Repeat until all notes are satisfactory

- [ ] **Step 4d: Verify note quality**

For each generated note file, check:
- [ ] File is valid Markdown (no syntax errors)
- [ ] Starts with `> [!tip] 学习指南` callout
- [ ] Contains at least one definition or theorem section
- [ ] LaTeX formulas render (`$...$` and `$$...$$`)
- [ ] At least one mermaid code block for concept relations
- [ ] No `[TODO]`, `[TBD]`, `[PLACEHOLDER]` markers
- [ ] No decorative filler text ("让我们来看看", "有趣的是")
- [ ] Writing is concise, no "不是X而是Y" patterns
- [ ] `README.md` has a valid index table and mermaid knowledge graph

- [ ] **Step 4e: Re-run sync-course to verify incremental sync**

1. Say: "同步 DSAA2011 的资料" again
2. Verify: reports "新增 0 个文件, 跳过 N 个已有文件" (incremental works)
3. Verify: no files are re-downloaded

- [ ] **Step 4f: Fix any issues found during testing**

For each issue discovered in steps 4a–4e:
1. Fix the corresponding skill file (sync-course.md or write-course-notes.md)
2. Delete the relevant output directory
3. Re-run the test step
4. Repeat until the issue is resolved

Document all issues found and fixes applied in a commit message.

- [ ] **Step 4g: Commit acceptance test results**

```bash
git add -A
git commit -m "test: DSAA2011 end-to-end acceptance test — sync-course + write-course-notes validated"
```

---

## Self-Review

**Spec coverage check:**
- [x] sync-course 单课程模式 → Task 1 Step 2, Task 4a
- [x] sync-course 批量模式 → Task 1 Step 1
- [x] sync-course 增量同步 → Task 1 Step 2d, Task 4e
- [x] sync-course 分类下载 → Task 1 Step 2e
- [x] sync-course 公告归档 → Task 1 Step 2f
- [x] sync-course meta.json → Task 1 Step 2b
- [x] sync-course index.md → Task 1 Step 2h
- [x] write-course-notes 发现课件 → Task 2 Step 1
- [x] write-course-notes 用户确认三问 → Task 2 Step 2
- [x] write-course-notes 并行 Agent Team → Task 2 Step 3
- [x] write-course-notes Agent prompt 模板 → Task 2 Step 3
- [x] write-course-notes README.md 索引 → Task 2 Step 4
- [x] write-course-notes Obsidian callout + mermaid → Task 2 Step 3 prompt
- [x] _index.md 注册 → Task 3 Step 1
- [x] skill.md 路由 → Task 3 Step 2
- [x] DSAA2011 端到端验收 → Task 4

**Placeholder scan:** No TBD, TODO, or placeholder patterns found.

**Type consistency:** All file paths, directory names, and JSON field names are consistent across tasks.
