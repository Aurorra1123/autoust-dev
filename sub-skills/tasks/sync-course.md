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
1. `.venv/` exists with `canvascli` installed (test: `.venv/bin/canvascli version`)
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
mkdir -p data/sync/current
.venv/bin/canvascli courses 2>/dev/null > data/sync/current/courses.json
```

**Single-course mode**: Ask the user to confirm the course name (match from
`data/sync/current/courses.json`). Extract `course_id`.

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
`-` (e.g. `COURSE1234`). If `course_code` is empty, derive from the course name.

#### 2b. Write meta.json

```bash
.venv/bin/python -c "
import json, datetime
course = json.load(open('data/sync/current/courses.json'))
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

def classify(filename, folder=''):
    name = (filename or '').lower()
    path = (folder or '').lower()
    # Lab assignments: LA followed by digit → other
    if re.search(r'[-_]la\d', name):
        return 'other'
    # Exam/project materials → other
    if re.search(r'exam|project_announce|final_review|midterm_review', name):
        return 'other'
    # Lecture slides: L+digit, both -L and _L, PDF only
    if re.search(r'[-_]l\d{1,2}[_-]', name) and name.endswith('.pdf'):
        return 'lectures'
    # LA0 intro lecture
    if re.search(r'-LA0\.pdf$', name):
        return 'lectures'
    # Books and references
    if name.startswith('book ') or name.startswith('reference'):
        return 'readings'
    # Fallback patterns
    if re.search(r'lecture|lec|课件|slide|week\s*\d', name + ' ' + path):
        return 'lectures'
    if re.search(r'reading|paper|article|论文|ref|bib', name + ' ' + path):
        return 'readings'
    return 'other'
```

Download each file:

```bash
.venv/bin/canvascli download <FILE_ID> -o "$COURSE_DIR/materials/<CATEGORY>/<FILENAME>"
```

#### 2f. Archive announcements

```bash
.venv/bin/canvascli announcements --course-id "$COURSE_ID" 2>/dev/null > /tmp/course_announcements.json
.venv/bin/python -c "
import json
course_ann = json.load(open('/tmp/course_announcements.json'))
course_ann = course_ann if isinstance(course_ann, list) else []
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
    fname = f.get('display_name', f.get('name', f.get('filename', '')))
    folder = f.get('folder', '')
    # Use same classify logic as 2e
    import re
    def classify(fname, folder=''):
        n = (fname or '').lower()
        p = (folder or '').lower()
        if re.search(r'[-_]la\d', n): return 'other'
        if re.search(r'exam|project_announce|final_review|midterm_review', n): return 'other'
        if re.search(r'[-_]l\d{1,2}[_-]', n) and n.endswith('.pdf'): return 'lectures'
        if re.search(r'-LA0\.pdf$', n): return 'lectures'
        if n.startswith('book ') or n.startswith('reference'): return 'readings'
        if re.search(r'lecture|lec|课件|slide|week\s*\d', n + ' ' + p): return 'lectures'
        if re.search(r'reading|paper|article|论文|ref|bib', n + ' ' + p): return 'readings'
        return 'other'
    cat = classify(fname, folder)
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
    fname = f.get('display_name', f.get('name', f.get('filename', '')))
    folder = f.get('folder', '')
    name = fname.lower()
    path = folder.lower()
    if re.search(r'[-_]la\d', name): cat = 'other'
    elif re.search(r'exam|project_announce|final_review|midterm_review', name): cat = 'other'
    elif re.search(r'[-_]l\d{1,2}[_-]', name) and name.endswith('.pdf'): cat = 'lectures'
    elif re.search(r'-LA0\.pdf$', name): cat = 'lectures'
    elif name.startswith('book ') or name.startswith('reference'): cat = 'readings'
    elif re.search(r'lecture|lec|课件|slide|week\s*\d', name + ' ' + path): cat = 'lectures'
    elif re.search(r'reading|paper|article|论文|ref|bib', name + ' ' + path): cat = 'readings'
    else: cat = 'other'
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
