# AutoStudy 踩坑记录

> 把这一轮搭抓取器时遇到的真实问题记下来，避免下次（或者别人接手时）重蹈覆辙。
> 按"环境 / Canvas API / playwright / 代码组织"分类。

---

## 环境 & Claude Code 通道

### 0. 新用户初始化不要把示例路径当默认路径

**现象**：用户为了模拟首次体验，先在 Claude Code / Codex 里打开了一个空白项目文件夹，然后要求下载并初始化 AutoStudy。agent 没有把这个空白文件夹理解为用户选定的落点，而是按 README 示例把仓库 clone 到 `~/workspace/autoust-dev`。

**根因**：入口文档只强调"dedicated clone"，并给了 `~/workspace/autoust-dev` 示例，但没有明确 clone 落点选择协议。agent 容易把示例路径升级成默认路径。

**规则**：
- 当前 agent workspace 是用户为初始化打开的空白文件夹时，优先 `git clone https://github.com/Aurorra1123/autoust-dev.git .`。
- 当前目录已经是 AutoStudy 仓库时，直接在该目录初始化。
- 当前目录非空且不是 AutoStudy 仓库，或当前工作区不明确时，先问用户目标目录。
- `~/workspace/autoust-dev`、桌面、下载目录等只能在用户明确指定时使用，不能作为静默默认值。

### 1. `! ` 前缀 Bash 没有 TTY，`input()` 立刻 EOF

**现象**：脚本里有 `input("Press Enter...")`，在 Claude Code 提示框里用 `! .venv/bin/python xxx.py` 跑，立刻报 `EOFError: EOF when reading a line`。

**根因**：Claude Code 的 `! ` 通道是把命令丢进 bash 但 stdin 被吃掉了，不是真终端。

**不要试**：`/dev/tty` fallback。在 Claude Code 的 `! ` 通道下 `/dev/tty` 直接 `OSError: Device not configured`，连真实 tty 都没法连。

**正确做法**：
- 设计脚本时**首选无交互的 CLI 参数模式**（`--course-id 2151 --folder-id 66610 --execute`），让 agent 通过 Bash 调用
- 实在需要等用户操作时，用**轮询**代替 `input()`（见下一条）
- 交互式 `--interactive` 模式可以保留，但只在真终端（iTerm / Terminal.app）里能跑，不能依赖它

### 2. 浏览器弹出 + 等用户登录：用轮询，不要 `input()`

**现象**：`login.py` 第一版用 `input("Press Enter after login is complete... ")` 让用户登录完按回车 —— 在 Claude Code 通道下直接 EOF。

**正确做法**：每 2 秒轮询 `/api/v1/users/self`，返回 200 + 带 `id` 的 JSON 就视为登录完成，自动保存 storage_state。10 分钟超时。代码见 `scraper/login.py`。

### 3. 装 chromium 慢 → 设代理

**现象**：`playwright install chromium` 直接走默认源极慢。

**解法**：用户本地有 `http://127.0.0.1:6666` 代理，所有相关环境变量都设上：
```bash
export http_proxy=http://127.0.0.1:6666 https_proxy=http://127.0.0.1:6666 \
       HTTP_PROXY=http://127.0.0.1:6666 HTTPS_PROXY=http://127.0.0.1:6666
.venv/bin/playwright install chromium
```

### 4. headless shell ≠ chromium

**现象**：`playwright install chromium` 默认装的是 `chromium_headless_shell`，**没有有头浏览器**。`login.py` 想 `launch(headless=False)` 让用户操作 —— 失败。

**解法**：再跑一次 `playwright install chromium --with-deps`（macOS 上 `--with-deps` 静默没效果，但 chromium 完整版会装上）。两个目录共存：
```
~/Library/Caches/ms-playwright/
├── chromium-1217                  # 完整版（有头登录用这个）
└── chromium_headless_shell-1217   # 只能跑 headless
```

---

## Canvas API

### 5. `enrollment_state=active` 是个陷阱

**现象**：`GET /api/v1/courses?enrollment_state=active` 返回 0 门课。但用户明明在读书、有 31 门课。

**根因**：未知 —— 可能是 HKUST(GZ) 的 enrollment 数据状态不符合 Canvas 默认的 active 判定。

**解法**：**不要传 `enrollment_state`**。拉全量后在客户端按 `workflow_state == "available"` 过滤。默认学期范围属于 `canvascli` 数据层的 CLI contract，AutoStudy 不应在 skill/task 文档里重写这套判断；用户明确要查历史学期时，用 `--term`。

```python
# 错
courses = client.paginate("/api/v1/courses", {"enrollment_state": "active"})

# 对
all_courses = client.paginate("/api/v1/courses", {"include[]": "term"})
courses = [c for c in all_courses
           if c.get("workflow_state") == "available"]
```

### 5b. Announcements 有隐式日期窗口，不要在 AutoStudy 里重写 REST

**现象**：Canvas announcements API 默认会套一个日期窗口。AutoStudy 如果直接调
REST 或先抓全局公告再在 Python 里按 course_id 过滤，可能只拿到 Canvas 默认窗口，
漏掉当前学期早期公告。

**根因**：公告范围需要结合 Canvas term/course dates。fixed `canvascli` 已把这件事
收在 CLI contract 里：`announcements --course-id <cid>` 默认先用
`term.start_at` / `term.end_at` 推导 latest active term 的完整 snapshot；term dates
不完整时再 fallback 到 course `start_at` / `end_at`；只有 term 和 course dates 都不完整时，
才让 Canvas 使用默认 announcements window。

**规则**：
- AutoStudy skill/task 文档只依赖 `canvascli announcements --course-id <cid>`、
  `--start-date`、`--end-date`、`--term` 这些 CLI contract。
- 不要在 AutoStudy 里复制 Canvas REST workaround、拼 date range、或恢复"全局
  announcements 后 Python 过滤"的流程。
- 用户不需要知道 Canvas internal course id；agent 先用 `courses` 解析课程名/代码，
  再把解析出的 id 传给 `--course-id`。

### 6. 不能假设每门课都开了 Canvas 全部功能

**现象**：拉 `/api/v1/courses/:id/quizzes` 时大部分课返回 **404**，不是空数组。

**根因**：老师可以在课程设置里关闭某些 tab（Quizzes / Modules / Discussions / Announcements）。关闭后这个端点根本不存在，返回 404。

**解法**：把 404 当作"该功能未启用"，静默吞掉，不要打 ERROR：
```python
try:
    quizzes = c.paginate(f"/api/v1/courses/{cid}/quizzes")
except RuntimeError as e:
    if "404" in str(e):
        quizzes = []  # feature disabled
    else:
        raise
```

**附带观察**（HKUST(GZ) 2025-26 Fall 当前学期 6 门课的实际开启情况）：
| 资源 | 开启课程数 |
|---|---|
| Assignments | 6/6 |
| Files | 6/6 |
| Announcements | 0/6 ← 学校老师好像都不用 Canvas 发公告 |
| Modules | 3/6 |
| Quizzes | 1/6 |
| Discussions | 4/6 |

启示：**Files 才是真正的数据底座**，Modules 是辅助索引（老师不一定整理）。

### 6b. `assignment.description` 不是完整 spec — 必须逐源侦查

**现象**：MVP 第一轮跑 4 个旗舰场景，agent 产出的 `solution.md` 里全是 `[PROBLEM N]` 占位符，`report.md` 写着 `[TODO: align with actual project spec]`，`slides.pdf` 是 `[此处由小组成员填入选题]`。pipeline 跑通了，作业没做。

**根因**：`canvascli assignment <id> -c <cid>` 拿回的 JSON 里 `description` 字段经常长这样：

```html
<p><a class="instructure_file_link"
      title="DSAA2043_Assignment_1.pdf"
      href="...files/475078?wrap=1"
      data-api-endpoint="...api/v1/courses/2151/files/475078"
      data-api-returntype="File">DSAA2043_Assignment_1.pdf</a></p>
```

真题（5 道证明题 + 数学定义 + recurrence）在 `DSAA2043_Assignment_1.pdf` 里。Agent 第一轮把 `description` 当题目读，结果只看到一个文件链接，写出来的就是把作业标题换种说法。后来又遇到 DSAA2011 Project：assignment description 是空的，真正项目说明在 module item PDF 里；UCUG1505 FINAL project 则是 assignment description 和 Week 4 module item 都指向同一个 Google Doc spec。

**正确做法**：`do-homework.md` routes clean starts to
`background-recon.md`. That first-stage flow fetches broad Canvas raw snapshots,
including announcements, then always runs `reference_collector` to preserve
task-relevant original source evidence under `references/`. The Main Agent
reads complete preserved references and writes terminal reconnaissance artifacts
before source confirmation and the planner handoff.
Do not revive `metadata_scout -> reading_plan.compact.json -> content_scout ->
source_findings.compact.md`.

**规则强化**（写进 `skill.md` Safety #7 + `do-homework.md` Safety #7）：deliverable 文件里**禁止出现** `[PROBLEM N]` / `[TODO: align...]` / `[此处由小组成员填入...]` 这种占位符。只允许 `[CITATION NEEDED: ...]` 和 `[CLARIFICATION NEEDED: ...]` 两种 marker，且都要在 do-homework `[E]` 一次性回流给用户。

### 6b-2. proposal framework is not complete reconnaissance

**现象**：开放式 proposal / research project 作业里，Canvas 可能直接给一个
proposal template 或 final project 文件。Agent 如果只读这两个文件，通常只能拿到
交付物框架，却不知道老师在课堂材料里怎么讲选题、research question、literature
review、field research、questionnaire、timeline、topic scope，最后写出来的方案会
有结构但没有课程方法论。

**根因**：proposal/research/open-ended 作业的完整 spec 往往是组合型的：
assignment shell 定义提交物，proposal/final-project 文件定义框架，methods 或
topic-selection 课件定义如何选择课堂相关主题和研究路径，同周主题材料提供可选的
supporting context。只读 proposal framework 会把“文件格式”误当成“作业理解”。

**正确做法**：`background-recon.md` fetches broad Canvas raw snapshots, including
announcements, then runs `reference_collector`. The collector preserves
assignment/spec evidence, methods/topic-selection evidence, and any relevant
syllabus, page, announcement, PDF, deck, or external source under `references/`
with `references/REFERENCE_INDEX.md` as the source evidence interface.
Canvas-native requirements must be copied verbatim under
`references/canvas_native/` or pointed back to the raw `canvas/*.json` snapshot.
proposal/research/open-ended 任务在 `review_a.json.verdict == "proceed"` 前，必须有
assignment/spec body evidence，并且要有 methods/topic-selection evidence，或者明确记录课程
没有可用方法指导。主代理完整读取 preserved references 和 direct-spec strong match，然后自己写
`review_a.json` 做 parent self-check，不靠临时手动补读救场。Do not recreate
`metadata_scout`, compact reading plans, `content_scout`, or compact source
findings as the normal source interface.

### 6c. Notebook 有图、report 没图：这是工具接口断裂

**现象**：DSAA2011 Project 的 notebook 生成了 12 张 PNG，slides 也嵌了图，但
`draft/report.md` 没有任何图片引用，`pdfimages` 显示
`report_G01_dropout.pdf` 里 0 张嵌入图片。验证只检查了 report 文本覆盖任务，
于是 text-only report 被当成 acceptable risk。

**根因**：
- notebook 代码直接 `plt.savefig('tsne_2d.png')`，把图平铺到 `draft/`
- `writing-helper.md` 只提示读取 `figures/fig_N.*`，没有扫描/整理 `draft/*.png`
- report quality review 没把“有可用实验图但 report 未嵌入”视为可自动修复质量问题

**正确做法**：
- notebook / figure-maker 输出统一进 `draft/figures/`
- `draft/report.md` 用相对路径引用：`![caption](figures/tsne_2d.png){width=70%}`
- ML/data report 至少嵌入支撑主要结论的代表图（t-SNE、clustering、confusion/ROC、feature importance 等）
- 若已有图但 report 没嵌，分类为 `auto_fixable`，触发 report/asset repair stage

### 6d. Pandoc + XeLaTeX 默认不保留中间 `.tex`

**现象**：`report_G01_dropout.pdf` 的 metadata 显示 `Creator: LaTeX via pandoc`
和 `Producer: xdvipdfmx`，但 workbench 里找不到 `.tex` / `.log`。

**根因**：`pandoc --pdf-engine=xelatex` 走 native PDF 路径时会用临时 TeX
文件，成功后默认清理；不是 AutoStudy 特意删除了原始 XeLaTeX 文件。

**正确做法**：
- PDF stage receipt 记录渲染引擎：`pandoc+xelatex` / `pandoc->tectonic` / fallback
- 需要 provenance 时额外写 `draft/render/<report>.tex` 和日志
- 渲染带图 markdown 时加 resource path，确保 `figures/foo.png` 能找到

### 6e. 连续大图不是只要 `pdfimages` 有图就算通过

**现象**：DSAA2011 clean-start report 里，clustering 小节的第一张 t-SNE
cluster 图从 page 2 底部开始，被页面边界裁掉；下一页只看到第二张 Ward 图。
`pdfimages -list` 仍然显示图片已嵌入，所以单靠 image embedding 检查会误判通过。

**根因**：
- Markdown 连续写两张大图，Pandoc 转成两个独立 LaTeX `figure` float
- 第一张图位于一个已经接近满页的位置，LaTeX 在 float 输出时产生
  `Overfull \vbox ... while \output is active`
- 质量审查只看了 PDF 元数据、`pdfimages` 和部分文本，没有视觉检查对应页面

**正确做法**：
- 多图 report 保留 `draft/render/*.tex` 和 `.log`，不要只保留 PDF
- 渲染日志出现 figure 附近的 `Overfull \vbox` 时，必须打开相关页面或渲染
  page screenshot 检查是否裁切/漂移
- 连续大图要么缩小并分组为一个原子 LaTeX figure block，要么加清晰的
  page/float boundary，确保图、caption 和讨论在合理位置
- 修复后重新跑 `pdfinfo`、`pdfimages -list`、`pdftotext` caption 顺序检查，
  并视觉检查 affected pages

**HKUST(GZ) 6 门课当前学期附件分布观察**（grep `assignment.description` 里的 `/files/`）：
- 96 个 assignments 里有 ~70% 的 description 包含至少一个 PDF / DOCX 链接
- 群组作业 (UCUG) 通常附件是题目说明 + rubric；lab 类作业附件是数据集 + 题目
- 极少有老师把题目正文直接粘到 Canvas WYSIWYG 里

启示：**没有 Copilot 式 background recon 这一步，整个 homework flow 就是个 pipeline demo**，不是真能做作业的工具。

### 7. Canvas REST API 直接带 cookie 调，不用 OAuth token

**好消息**：用 playwright 的 storage_state 保留登录 cookie 后，所有 `/api/v1/*` 端点都能直接调，返回 JSON。**不需要申请 personal access token、不需要 OAuth、不需要解析 HTML DOM**。

```python
ctx = browser.new_context(storage_state="canvas_state.json")
resp = ctx.request.get("https://hkust-gz.instructure.com/api/v1/users/self")
data = resp.json()  # 直接拿 dict
```

这比 AutoPku 用 `pku3b` CLI + ANSI 色码正则解析的路径干净得多。

### 7b. `canvascli init` 不是登录态检查；`state.json` 和 SSO remember-login 是两层

**现象**：用户怀疑频繁登录是因为 SSO 页面没有勾选 "remember login"。验证时误把 `canvascli init` 当成"测试是否还需要登录"来跑，结果它必然打开浏览器，制造了错误信号。

**正确模型**：

- `canvascli init` 是显式登录 / 刷新命令：打开浏览器，完成 SSO，写入新的 `~/Library/Application Support/canvascli/state.json`。
- `canvascli whoami` 才是状态检查：它读取现有 `state.json`，成功返回用户对象就说明当前 session 可用。
- `state.json` 是否生成只取决于本次 `init` 是否成功完成 SSO；和是否勾选 remember-login 没有直接关系。
- SSO 的 "remember login" / "trust this browser" 影响的是**下一次重新走 SSO 时是否能快速通过**。不勾也会生成可用的 `state.json`，但下次 state 过期或刷新时可能又要完整登录。

**验证记录（2026-06-01）**：

- 当前有效 `state.json` 下，`.venv/bin/canvascli whoami --pretty` 正常返回 Canvas 用户信息，无需浏览器。
- 移走 `state.json` 后跑 `canvascli init`，不勾 remember-login 仍会生成新的 `state.json`。
- 再次移走该 `state.json` 后跑 `init`，SSO 需要重新手动登录。
- 用户之后勾选 remember-login 生成的 state 可被 `whoami` 正常使用；这说明日常命令依赖的是 `state.json`，不是每次重新 SSO。

**规则**：文档和 agent 流程里，永远用 `whoami` / 实际读命令检查登录态；只有 `No saved session`、`session expired`、HTTP 401 时才让用户跑 `init`。运行 `init` 时提醒用户勾选 remember-login / trust-this-browser。

### 8. 分页用 Link header，不要瞎设 `page` 参数

Canvas 的分页是 HTTP Link header 标准：
```
Link: <...?page=2>; rel="next", <...?page=5>; rel="last"
```

要写一个 `paginate()` 通用方法跟着 `rel="next"` 走，直到没有 next。`per_page=100` 是单页上限。代码见 `scraper/api.py:CanvasClient.paginate`。

### 9. 文件夹结构靠 `parent_folder_id` 自己重建

**现象**：`/api/v1/courses/:id/folders` 返回扁平列表，每个 folder 有 `parent_folder_id`，但没有现成的树。

**解法**：自己 O(n) 重建。`parent_folder_id == None` 的是 root（注意不是 `0` 也不是空字符串，是 JSON `null` → Python `None`）。代码见 `scraper/api.py:folder_tree`。

### 10. 文件名 / 文件夹名带空格和中文

**例子**：`course files`、`DSAA_2043_Spring_2025_Midterm_Exam`、`UCUG 1077 syllabus.docx`、`1# Week UCUG1809 20250902 Pre-session Task.docx`。

**解法**：
- 路径用 `pathlib.Path` 而不是字符串拼接
- shell 调用时所有路径**带引号**：`ls "data/files/DSAA2043 (L01)/..."`
- 写一个 `safe_name()` 函数只替换系统禁字符 `/ \ : * ? " < > |`，保留中文和空格

```python
def safe_name(s):
    s = (s or "").strip()
    s = re.sub(r'[/\\:*?"<>|]', "_", s)
    return s[:120] or "untitled"
```

---

## 代码组织

### 11. `scraper/` 既要支持 `python scraper/xxx.py` 又要被外部 import

**问题**：脚本里写 `from api import ...` —— 直接跑没问题，但外部 `from scraper.download import ...` 会报 `ModuleNotFoundError: No module named 'api'`。

**当前临时解法**：测试代码里 `sys.path.insert(0, "scraper")` 兜底。

**未来更正确的做法**（写 skill 时再做）：把 `scraper/` 变成正式 package（加 `__init__.py`），统一用 `python -m scraper.xxx` 跑，import 改成相对 import (`from .api import ...`)。

### 12. 状态文件 / 认证文件 / 数据文件 要分目录

```
~/Library/Application Support/canvascli/state.json  # Canvas 登录态（绝对不能进 git）
data/sync/current/*.json                            # 最近一次 sync-status 当前快照
data/runs/<date>/raw/*.json                         # 某次 scan-plan 使用过的快照副本
data/courses/<course>/materials/...                 # 下载的课件
.venv/                                              # python 虚拟环境
```

`.gitignore` 全部排除前面四个。

### 13. dry-run 默认 + `--execute` 显式开关

**经验**：下载是有副作用的操作（写磁盘 + 写 state）。脚本 CLI 模式默认应该是 **dry-run**（只 print plan），加 `--execute` 才真的下载。这样误操作不会污染状态。

```bash
# 默认只看 plan
python scraper/download.py --course-id 2151 --folder-id 66610

# 显式 --execute 才真下载
python scraper/download.py --course-id 2151 --folder-id 66610 --execute
```

### 14. 函数式接口 + CLI 包装的双层设计

**问题**：交互式 `_pick / _confirm` 在 Claude Code 通道下跑不了，但又不能完全没有交互能力。

**解法**：核心逻辑写成**纯函数**（`list_courses` / `list_folder_tree` / `plan_download` / `execute_download`），CLI 和 `--interactive` 都只是这些函数的薄包装。这样：
- skill agent 可以直接 import + 配合 `AskUserQuestion` 用
- Bash 调用走 CLI 参数模式
- 真终端用 `--interactive`

三种入口共享同一套逻辑，互不耦合。

---

## 留给将来的事

- [ ] `scraper/` 正式打包成 module（加 `__init__.py`，改相对 import）
- [ ] 拉 submission 详情（看老师评语、附件、分数）
- [ ] HTML 化的 `message` 字段（announcements / discussions）需要 sanitize 再喂给 LLM
- [ ] 大文件下载加进度条（现在 100MB 的 PDF 静默等很久）
- [ ] storage_state cookie 过期处理（现在过期会全员 401，需要捕获并提示重跑 `login.py`）

---

*最后更新：2026-05-24*
