# AutoStudy 宣发想法

> 用来对外讲清楚 "AutoStudy 能干什么"。
> 五个核心场景是**对外宣传的主舞台**，不一定等于功能上线顺序，但它们决定了 M3 阶段最该打磨的 demo。

---

## 五大宣传场景

按"用户能立刻看到产物"的标准选的，不是按技术难度排的。

### 1. 写论文 / Report

**场景**："帮我完成 DLED3020 的 paper critique"

**需要的能力组合**：
- 文献搜索 (paper-search)
- 论文阅读 + 摘要 (pdf-reader)
- 数据可视化 (figure-maker)
- 学术写作（含引用格式 APA / IEEE）(writing-helper)
- PDF 排版 (pdf-renderer)

**对外展示点**：从一句话指令 → 出一份带图表 + 引用的完整 PDF。

**适配课程**：
- DLED3020 — Academic English（paper critique / essay）
- UCUG1809 — Sociology（reflective essay）
- DSAA3051 — NLP（research report）

---

### 2. 做 PPT / Presentation

**场景**："帮我把 UCUG1077 的 literature review 做成 group presentation"

**需要的能力组合**：
- 内容大纲 (writing-helper 改造)
- 配图生成 (figure-maker)
- Slide 渲染 (slide-maker，技术路径：marp / reveal-md / 真正的 PPTX)
- 输出多种格式：PDF / PPTX / HTML

**对外展示点**：从已有的文档/笔记 → 出一份能直接上台的 slides。

**适配课程**：
- UCUG1077 — Chinese Communication（presentation 占比高）
- DSAA2012 — Deep Learning（project final presentation）
- 几乎所有 group project 类

**风险**：PPTX 格式生成质量取决于工具链，marp/reveal 出 HTML/PDF 美观度可控；要直接出 .pptx 要看 python-pptx 能不能做到老师能接受的水平。

---

### 3. 视频剪辑 / 多模态

**场景**："把我录的 lecture recording 剪个 5 分钟摘要 + 配字幕" 或 "用 manim 把这道证明题做个 30 秒动画"

**需要的能力组合**：
- 视频处理 (ffmpeg 工具链)
- 字幕生成 (whisper.cpp 本地)
- 教学动画 (manim — 数学/CS 概念可视化)
- 配音 (TTS，可选)

**对外展示点**：这是**最具传播力**的一个场景 —— 视频比 PDF 更容易在社交媒体上炸。

**适配课程**：
- 录制 / 总结 lecture 内容
- 做 group project 的 demo 视频
- DSAA2012 / DSAA2043 用 manim 可视化概念

**风险**：技术栈最复杂（ffmpeg + manim + whisper 都不轻）。建议作为 M3 阶段**最后一个**实现的场景，前面四个稳了再做。但**宣传时一定要带上**，因为这是杀手锏。

---

### 4. 数学作业（LaTeX + PDF）

**场景**："帮我完成 DSAA2043 hw3，5 道动态规划证明题"

**需要的能力组合**：
- 题目识别 + 解析 (pdf-reader)
- 数学推理 + 证明 (proof-solver)
- LaTeX 排版（含中文支持 + 算法伪代码 + tikz 图）(math-renderer / pdf-renderer)
- 自动校对（公式编号、引用、定理环境）

**对外展示点**：最能体现 "agent 真的理解了题目"，不是只做表面 paraphrasing。这个能直接打"自动做题"的核心叙事。

**适配课程**：
- DSAA2043 — Algorithms（DP/图论证明）
- DSAA3051 — NLP（数学+coding 混合）
- AIAA2711 — Math for AI
- UFUG2103 — Linear Algebra
- UFUG1106 — Calculus

**注意**：这是最容易被认为"是不是作弊"的场景。宣传文案里要明确**强调 design 审核环节**和**"agent 做完后你必须复核"**的态度。

---

### 5. 实验 / Lab 课代码自动完成

**场景**："帮我完成 DSAA2012 lecture 3 的 lab —— 实现一个 ResNet"

**需要的能力组合**：
- Lab spec 解析 (pdf-reader)
- 代码生成 (code-writer)
- 单元测试自动跑 (test-runner)
- 注释 + 报告 (writing-helper 改造 → lab report)
- Notebook 输出 (.ipynb)

**对外展示点**："从 lab spec 到能跑的代码 + 报告，agent 帮你做完整个 lab"。

**适配课程**：
- DSAA2012 — Deep Learning（lab + project）
- DSAA2043 — Algorithms（OJ + lab）
- UFUG1601 — Intro CS
- UFUG2601 — C++ Programming
- UFUG2602 — Data Structures

**风险**：涉及 OJ 提交（见 ROADMAP "第三方链接处理原则"），默认走"本地生成 → 学生手动复制提交"，不直接打通 OJ。

---

## 宣传文案核心叙事

**短版（一句话）**：
> AutoStudy = 在 Claude Code 里跑的 HKUST(GZ) 学业 agent — 同步 Canvas、写论文、做 PPT、剪视频、做数学题、跑 lab 代码，一句话搞定。

**中版（一段话）**：
> 你打开 Claude Code，告诉它："帮我完成 DSAA2043 hw3 的所有证明题，做成 LaTeX 排好版的 PDF，然后通过 Canvas 提交。"
> 几分钟后，你看到一份完整答案、引用了 lecture slides 的相关定理、附带了 tikz 图、还自带提交回执。
> 这不是 ChatGPT 对话框 — 这是一个能调用文献搜索、画图、写代码、渲染 PDF、操作教学网的 **agent 编排系统**，你只是它的项目经理。

**长版（用于 README / blog post）**：
- 区别于 ChatGPT 网页对话的三大痛点：知识碎片化、文件管理混乱、不可定制
- 区别于 AutoPku 的三大差异：HKUST(GZ) 场景 / 启发式 skill 调度 / 反问式学习
- 五大演示场景（上面五个）+ 各自一段 demo gif / 视频

---

## 对外发布的优先级（草拟）

按"打磨成本 vs 宣传效果"排：

| 场景 | 打磨成本 | 宣传效果 | M3 内顺序建议 |
|---|---|---|---|
| 写论文 / Report | 中 | 高 | 1 — 首发 |
| 数学作业 LaTeX | 中 | 极高（直接打"做作业"叙事） | 2 |
| Lab 代码 | 高（涉及测试） | 高 | 3 |
| 做 PPT | 中（marp 路径稳） | 中 | 4 |
| 视频剪辑 | 极高（manim/ffmpeg） | 极高（社交传播炸点） | 5 — 留作宣传重磅 |

每个场景完工时都准备：
- 一段 30 秒 demo 视频（screencast + 终端实录）
- README 上加一张静态截图
- 一个真实作业的产出文件作为示例（脱敏后）

---

## 用户画像（用来校准宣传调性）

**主力受众**：
- HKUST(GZ) 在读本科生（首批种子用户）
- 已经会用 ChatGPT 但还没用过 Claude Code / coding agent 的人
- 痛点：作业多、ddl 紧、想用 AI 但不知道怎么用得深

**次级受众**：
- HKUST(GZ) 研究生 / 老师（看到学生在用会好奇）
- 其他 Canvas-based 学校的学生（HKUST 本部 / 海外校）—— 抓取器换个 base URL 就能复用
- AI agent / skill 生态的关注者（GitHub trending 这条路）

**调性**：
- 不夸张说 "agent 完全代写"，强调 **"agent 负责脏活，你负责思考和审核"**
- 学术诚信红线要明确画出来 —— 我们不是帮你作弊，是帮你把时间花在思考上而不是排版上
- 中文为主，英文 demo 也要准备（HKUST(GZ) 双语环境）

---

## 不要在宣传里出现的承诺

避免以下话术（会被打脸）：

- ❌ "100% 自动通过任何作业" — 这是不可能的，避免预期失控
- ❌ "代替学生学习" — 触学术诚信红线
- ❌ "5 分钟解决一切" — 时间会因任务复杂度差异巨大
- ❌ "免费" — 用户得自带 Claude / Codex 的 API 用量
- ❌ "无需登录" — 必须 SSO 登录 Canvas

---

## 待补充

- [ ] 各场景的 demo 视频脚本（每个 30 秒）
- [ ] 学术诚信声明文案（README / about 页固定一段）
- [ ] 与教务 / IT 的沟通策略（如果有学校层面的反馈）
- [ ] 海外校 Canvas 适配的成本评估（M5 阶段考虑）

---

*最后更新：2026-05-13*
