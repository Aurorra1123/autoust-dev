# AutoStudy 踩坑记录

> 把这一轮搭抓取器时遇到的真实问题记下来，避免下次（或者别人接手时）重蹈覆辙。
> 按"环境 / Canvas API / playwright / 代码组织"分类。

---

## 环境 & Claude Code 通道

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

### 6b. `assignment.description` 经常只是一个 PDF 附件链接 — 必须下载附件才能读到真题

**现象**：MVP 第一轮跑 4 个旗舰场景，agent 产出的 `solution.md` 里全是 `[PROBLEM N]` 占位符，`report.md` 写着 `[TODO: align with actual project spec]`，`slides.pdf` 是 `[此处由小组成员填入选题]`。pipeline 跑通了，作业没做。

**根因**：`canvascli assignment <id> -c <cid>` 拿回的 JSON 里 `description` 字段经常长这样：

```html
<p><a class="instructure_file_link"
      title="DSAA2043_Assignment_1.pdf"
      href="...files/475078?wrap=1"
      data-api-endpoint="...api/v1/courses/2151/files/475078"
      data-api-returntype="File">DSAA2043_Assignment_1.pdf</a></p>
```

真题（5 道证明题 + 数学定义 + recurrence）在 `DSAA2043_Assignment_1.pdf` 里。Agent 第一轮把 `description` 当题目读，结果只看到一个文件链接，写出来的就是把作业标题换种说法。

**正确做法**：`do-homework.md [A3]` 必须调 `tools/problem-extractor.md`，把 description HTML 里的 `/files/<id>` 全部 grep 出来，用 `canvascli download <fid>` 下回来，pdftotext / pdfminer.six 抽文本，组装成 `problem.md`。下游 `writing-helper` / `code-writer` / `slide-maker` 只能读 `problem.md`，不准读 `assignment.json.description`。

**规则强化**（写进 `skill.md` Safety #7 + `do-homework.md` Safety #7）：deliverable 文件里**禁止出现** `[PROBLEM N]` / `[TODO: align...]` / `[此处由小组成员填入...]` 这种占位符。只允许 `[CITATION NEEDED: ...]` 和 `[CLARIFICATION NEEDED: ...]` 两种 marker，且都要在 do-homework `[E]` 一次性回流给用户。

**HKUST(GZ) 6 门课当前学期附件分布观察**（grep `assignment.description` 里的 `/files/`）：
- 96 个 assignments 里有 ~70% 的 description 包含至少一个 PDF / DOCX 链接
- 群组作业 (UCUG) 通常附件是题目说明 + rubric；lab 类作业附件是数据集 + 题目
- 极少有老师把题目正文直接粘到 Canvas WYSIWYG 里

启示：**没有 problem-extractor 这一步，整个 do-homework 就是个 pipeline demo**，不是真能做作业的工具。

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
.auth/canvas_state.json     # 登录态（绝对不能进 git）
.state/downloads.json       # 增量下载记录
data/courses.json           # 拉到的真实数据
data/files/<course>/...     # 下载的课件
.venv/                      # python 虚拟环境
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
