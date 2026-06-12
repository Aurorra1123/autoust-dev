---
name: large-scale-exploration-workflow
description: 大规模代码探索任务的最佳实践和工作流程
metadata:
  type: feedback
---

# 大规模探索工作流程改进

## 经验教训
**2026-06-03** - 在深入分析 AutoStudy 项目 M3.5 架构升级时，直接读取了大量文档和脚本，导致上下文占用过多，影响了效率和响应速度。

## 正确做法

### 1. 优先使用子代理进行并发探索
- 当任务涉及多个文件的阅读、分析或搜索时，**必须**使用 Agent 工具创建子代理
- 子代理可以并发处理多个探索任务，大幅提升效率
- 单次最多使用 6 个并发子代理（符合全局配置）

### 2. 任务分解策略
```
大型探索任务
├── Agent_1: 阅读核心文档 (skill.md, AGENTS.md, ROADMAP.md)
├── Agent_2: 分析最近提交和变更 (git log, git diff)
├── Agent_3: 检查关键脚本文件 (scripts/*.py)
├── Agent_4: 查看工具文档 (sub-skills/tools/*.md)
├── Agent_5: 查看任务文档 (sub-skills/tasks/*.md)
└── Agent_6: 分析协作文档 (COLLABORATION.md, canvas-pilot-reference.md)
```

### 3. 子代理创建模式
```python
# 正确：并发创建多个子代理
Agent({
    "description": "阅读核心文档",
    "prompt": "阅读 skill.md, AGENTS.md, ROADMAP.md 并总结项目架构和当前状态",
    "subagent_type": "Explore"
})

Agent({
    "description": "分析最近提交",
    "prompt": "分析最近的 git 提交，查看具体修改内容和影响",
    "subagent_type": "Explore"
})
# ... 其他并发任务
```

### 4. 协作模式
- 主代理负责总体协调和最终总结
- 子代理负责具体执行和细节分析
- 汇总所有子代理的发现，提供完整报告
- 上下文占用保持在合理水平

### 5. 适用场景
- 项目架构分析
- 大规模文档阅读
- 多文件变更审查
- 功能模块调研
- 技术债务评估

## 错误做法
- 单个代理 sequential 阅读大量文件
- 一次性读取过多文档内容
- 占用过多上下文空间
- 响应速度慢，效率低下

## 最佳实践
1. **Always** - 遇到大规模探索任务，首先考虑使用子代理
2. **Always** - 将任务合理分解为可并行的子任务
3. **Always** - 控制单次代理的上下文使用量
4. **Remember** - 子代理数量上限为 6 个
5. **Remember** - 主代理负责最终整合和决策

## 参考
- `mem:concurrent-subagents` - 并发子代理使用规范
- `mem:task-decomposition` - 任务分解策略
- `mem:context-management` - 上下文管理最佳实践