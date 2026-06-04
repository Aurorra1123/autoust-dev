# sync-course + write-course-notes 设计文档

> 日期：2026-06-04
> 状态：已批准
> 参考：AutoPku write-notes / agent-helpers / create-agent / _detect

## 一、背景

AutoStudy 当前所有数据围绕 do-homework 组织，课程本身没有持久化身份。用户需要：

1. 把课程资料（课件、公告、文件）持久化归档，独立于作业流程
2. 基于归档的课件 PDF 生成结构化课程笔记

两个 skill 作为固定流水线实现，独立于现有的动态管线 do-homework。

## 二、设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 独立 skill vs 扩展 sync-status | 独立 | sync-status 是作业计划器，sync-course 是课程归档器，职责不同 |
| 增量同步 vs 全量覆盖 | 增量 | 避免重复下载，利用 canvascli 自带的 downloads.json |
| do-homework 产物是否反写 courses/ | 否 | 两个数据流独立，单向消费 |
| 资料组织方式 | 按类型 | lectures/readings/other，直觉清晰 |
| 笔记输出格式 | Obsidian 风格 Markdown | callout + mermaid，不强制 PDF 渲染 |
| 并行策略 | 每课件一个 Agent | 参考 AutoPku write-notes，同构任务天然并行 |
| 运行时适配 | 暂不引入 | YAGNI，M5 再做，Agent prompt 模板保持独立可迁移 |

## 三、sync-course 设计

### 3.1 文件位置

`sub-skills/tasks/sync-course.md`

### 3.2 触发方式

| 用户意图 | 模式 |
|----------|------|
| "同步 DSAA2043 的资料" / "下载 XX 课的课件" | 单课程 |
| "同步所有课程资料" / "下载全部课件" | 批量（本学期所有课） |

### 3.3 执行流程

```
[A] 环境检查
    .venv/bin/canvascli --version
    .venv/bin/canvascli whoami
    → 失败则重定向到 canvascli-setup.md

[B] 课程发现
    canvascli courses → 获取课程列表
    单课程：用户确认课程名 → 匹配 course_id
    批量：列出所有课程 → 用户确认范围（AskUserQuestion）

[C] 单课程同步循环（批量时对每门课重复）

    C1: 创建目录
        data/courses/<COURSE>/{materials/{lectures,readings,other},canvas_sync,notes}

    C2: 写 meta.json
        {"name": ..., "course_code": ..., "term": ..., "course_id": ..., "synced_at": ...}

    C3: 拉取文件清单
        canvascli files --course-id <CID> > canvas_sync/files_index.json

    C4: 增量对比
        对比已有 files_index.json 和新拉取的
        提取新增文件 + 更新文件（file_id + updated_at 变化）
        已有文件跳过

    C5: 分类下载
        根据文件名/Canvas folder 路径匹配类型：
        - 含 lecture/lec/L数字/课件/slide → materials/lectures/
        - 含 reading/paper/article/论文/ref → materials/readings/
        - 其他 → materials/other/
        使用 canvascli download（单文件或文件夹模式）

    C6: 公告归档
        canvascli announcements → 过滤该课程
        追加写入 canvas_sync/announcements.json（不覆盖历史）
        去重：按 announcement_id 去重

    C7: Module 结构
        canvascli modules --course-id <CID> → canvas_sync/modules.json

    C8: 生成 index.md
        课程信息 + 资料清单（按类型分组）+ 公告摘要 + 上次同步时间

[D] 汇报结果
    展示：新增 X 个文件，更新 Y 个文件，跳过 Z 个已有文件
```

### 3.4 数据结构

```
data/courses/<COURSE>/
├── meta.json                    # 课程元信息
├── canvas_sync/
│   ├── files_index.json         # Canvas 文件清单（含 file_id, filename, updated_at, size, folder）
│   ├── announcements.json       # 公告归档（累积，按 announcement_id 去重）
│   └── modules.json             # Module 结构
├── materials/
│   ├── lectures/                # 课件 PDF
│   ├── readings/                # 阅读材料
│   └── other/                   # 其他资料
├── notes/                       # write-course-notes 产出（初始为空）
└── index.md                     # 课程总览（可人读）
```

### 3.5 meta.json 结构

```json
{
  "course_id": "2151",
  "name": "DSAA2043 (L01) - Design and Analysis of Algorithms",
  "course_code": "DSAA2043",
  "term": "2025-26 Fall",
  "synced_at": "2026-06-04T14:30:00+08:00",
  "file_counts": {
    "lectures": 12,
    "readings": 5,
    "other": 3
  }
}
```

### 3.6 files_index.json 结构

```json
[
  {
    "file_id": 496305,
    "filename": "L01-introduction.pdf",
    "size": 1234567,
    "updated_at": "2026-05-20T10:00:00Z",
    "folder": "course files/Lectures",
    "local_path": "materials/lectures/L01-introduction.pdf",
    "category": "lectures"
  }
]
```

### 3.7 与 sync-status 的关系

完全独立。sync-status 拉作业数据 → plan.json → do-homework。sync-course 拉课程资料 → materials/ → write-course-notes。两者可以同时存在。

## 四、write-course-notes 设计

### 4.1 文件位置

`sub-skills/tasks/write-course-notes.md`

### 4.2 前置依赖

`data/courses/<COURSE>/materials/lectures/` 下有课件 PDF（sync-course 产出）。如果目录为空，提示用户先运行 sync-course。

### 4.3 执行流程（固定 4 步，参考 AutoPku write-notes）

```
[1] 发现课件
    扫描 data/courses/<COURSE>/materials/lectures/ 列出所有 PDF
    按 filename 排序（确保 L01 → L02 → ... 顺序）
    如果目录为空 → 提示先跑 sync-course

[2] 用户确认（AskUserQuestion，三问）
    Q1: 选择范围 — 全部课件 / 指定范围（列出文件让用户选）
    Q2: 详细程度 — 精简（核心定义定理）/ 标准（含证明思路）/ 详细（完整推导）
    Q3: 额外要求（多选）— LaTeX公式编号 / 概念关联图 / 例题

[3] 并行 Agent Team
    为每个选中的 PDF spawn 一个 Writer Agent：
    - 每个 Agent 独立：读 PDF → 筛选内容 → 写 Markdown 笔记
    - Agent prompt 模板固定（见 4.4）
    - 10 个课件 = 10 个 Agent 同时运行

[4] 汇总索引
    生成 data/courses/<COURSE>/notes/README.md：
    - 课程名 + 生成时间 + 详细程度
    - 笔记索引表（序号、标题、核心主题、文件链接）
    - 课程级 mermaid 知识图谱
    - 全局术语/符号速查表
```

### 4.4 Writer Agent Prompt 模板

参考 AutoPku write-notes 的 Writer Agent，适配 AutoStudy 上下文：

```
你是笔记撰写专家，从课件中提取核心学术内容。

输入：{pdf_path}
输出：{notes_dir}/{lecture_name}.md
详细程度：{detail_level}
额外选项：{extra_options}

## 引用工具
引用: sub-skills/tools/pdf-reader.md（使用 PyMuPDF 读取 PDF）

## 内容筛选原则

### 保留内容
- Motivation：为什么要研究这个问题？核心问题是什么？
- 定义：形式化定义、符号表示
- 定理/命题：精确陈述，编号
- 证明：关键步骤、核心技巧
- 结论：主要结果、推论
- 技术工具：关键引理、构造方法

### 去除内容
- 历史背景：谁发明的、发展历程
- 故事/轶事：装饰性内容
- 重复性内容：多处出现的相同解释
- 装饰性语言："让我们来看看"、"有趣的是"

### 写作反模式（严禁）
- "不是X而是Y"句式 → 直接说Y是什么
- 过度分段 → 能用一段话讲清楚的不要拆
- 废话填充 → 不要过渡句、重复换词

## 笔记格式（Obsidian 风格）

每节笔记遵循以下结构：

# {Lecture 标题}

> [!tip] 学习指南
> 本节核心：{一句话概括}
> 前置知识：{需要哪些前面的概念}
> 重点关注：{考试/理解的关键点}

## 核心问题/Motivation
## 定义（含 [!note] 直觉理解 callout）
## 定理与命题（含 [!warning] 易错点 callout）
## 概念关系（mermaid 图）
## 结论（含 [!tip] 复习要点 callout）
## 记号速查表

## 约束
- Obsidian callout 语法（> [!tip] / [!note] / [!warning] / [!example]）
- LaTeX 数学公式（$...$ 行内，$$...$$ 行间）
- mermaid 图替代纯文字关系描述
- 行文紧凑，目标读者是预习/备考的大学生
- 纯故事章节标注"本节为导言/背景，略"

返回：
- 处理页数
- 提取的定义数、定理数
- 输出文件路径
```

### 4.5 输出结构

```
data/courses/<COURSE>/notes/
├── README.md              # 课程级索引（知识图谱 + 术语表 + 笔记链接）
├── L01-introduction.md    # 每个课件一个笔记
├── L02-linear-algebra.md
├── L03-graph-algorithms.md
└── ...
```

### 4.6 README.md 模板

```markdown
# {课程名} 课程笔记

生成时间：{timestamp}
详细程度：{detail_level}
课件数量：{count}

## 笔记索引

| # | 讲次 | 核心主题 | 文件 |
|---|------|---------|------|
| 1 | L01 | 介绍 | [L01-introduction.md](./L01-introduction.md) |
| 2 | L02 | 线性代数 | [L02-linear-algebra.md](./L02-linear-algebra.md) |

## 课程知识图谱

​```mermaid
graph TD
    A[核心概念1] --> B[核心概念2]
    B --> C[定理1]
​```

## 术语/符号速查

| 符号 | 含义 | 首次出现 |
|------|------|---------|
| $O(n \log n)$ | 时间复杂度 | L02 |
```

## 五、与现有系统的集成

### 5.1 新增文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `sub-skills/tasks/sync-course.md` | Task Skill | 课程级资料同步 |
| `sub-skills/tasks/write-course-notes.md` | Task Skill | 课程笔记生成 |

### 5.2 修改文件

| 文件 | 修改 |
|------|------|
| `sub-skills/tools/_index.md` | 添加两个新 tool 的注册行 |
| `skill.md` | 添加两个新 task 的路由规则 |

### 5.3 不修改

- sync-status.md — 保持不变
- do-homework.md — 保持不变
- task-orchestrator.md — 保持不变
- data/homework/ — 保持不变

## 六、下游消费者

| 消费者 | 读什么 | 从哪读 |
|--------|--------|--------|
| write-course-notes | 课件 PDF | `courses/<COURSE>/materials/lectures/` |
| M4 学习助手（未来） | 笔记 + 公告 + 材料 | `courses/<COURSE>/notes/` + `canvas_sync/` |
| make-review-slides（未来） | 已有笔记或课件 | `courses/<COURSE>/notes/` 或 `materials/lectures/` |
| 用户自己 | 课程总览 | `courses/<COURSE>/index.md` |
