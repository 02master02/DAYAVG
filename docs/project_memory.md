# 项目记忆文档

## 1. 项目一句话概述

`DayAvg` 目前是一个刚完成工作流初始化的空白项目仓库。

## 2. 用户原始目标

用户希望当前项目采用 `vibe-coding-workflow` 的纪律化开发方式推进。

## 3. 当前任务目标

本轮目标是初始化项目结构与文档，而不是实现具体业务功能。

## 4. 当前项目状态

### 已完成

- 读取并采用 `vibe-coding-workflow` 技能要求
- 创建 `docs/`, `src/`, `tests/`, `outputs/` 基础结构
- 创建必需文档并写入初始内容
- 创建 `README.md` 与空白 `requirements.txt`

### 未完成

- 产品需求定义
- 业务代码实现
- 自动化测试框架
- 运行命令与依赖安装说明的具体化

### 当前可运行程度

当前是“可继续开发”的初始化状态，但还没有可运行的应用程序。

## 5. 重要文件与目录

| 路径 | 作用 | 当前状态 |
|---|---|---|
| `README.md` | 仓库入口说明 | 已创建 |
| `requirements.txt` | 依赖预留文件 | 已创建 |
| `docs/task_goal.md` | 任务目标与约束 | 已创建 |
| `docs/implementation_plan.md` | 结构设计与执行计划 | 已创建 |
| `docs/progress_log.md` | 进度记录 | 已创建 |
| `docs/project_memory.md` | 新对话交接文档 | 已创建 |
| `docs/usage.md` | 使用说明入口 | 已创建 |
| `src/` | 源码目录 | 已创建，暂为空骨架 |
| `tests/` | 测试目录 | 已创建，暂为空骨架 |
| `outputs/` | 输出目录 | 已创建，暂为空骨架 |

## 6. 输入与输出约定

### 输入

- 当前仅有用户自然语言需求
- 后续若有数据文件、配置文件或接口参数，应在 `docs/task_goal.md` 中补充

### 输出

- 说明性文档放在 `docs/`
- 业务源码放在 `src/`
- 测试代码放在 `tests/`
- 生成结果默认放在 `outputs/`

## 7. 核心设计思路

1. 先文档、后代码，避免需求漂移
2. 先搭建结构，再进入具体实现，避免把所有逻辑塞进单文件
3. 保持项目可交接，确保新会话能直接继续

## 8. 已做过的重要决策

| 决策 | 原因 |
|---|---|
| 本轮不实现业务功能 | 用户只启用了工作流技能，没有提供功能目标 |
| 手动创建文档而非运行技能脚本 | 当前环境中的 `python.exe` 不可直接执行 |
| 保留空 `requirements.txt` | 尚无依赖，但提前占位便于后续维护 |

## 9. 已踩过的坑和注意事项

- 运行 `python C:\Users\30787\.agents\skills\vibe-coding-workflow\scripts\init_vibe_project.py --help` 失败，错误是当前环境无法访问 `python.exe`
- 因此后续若想运行 Python 脚本，可能需要先确认解释器路径，例如 `py` 或具体虚拟环境解释器

## 10. 当前运行命令

```bash
# 尚无应用运行命令
```

## 11. 当前测试命令

```bash
# 尚无自动化测试命令
git status --short
Get-ChildItem -Recurse
```

## 12. 当前依赖

```bash
# 无
```

## 13. 下一步任务

1. 明确 `DayAvg` 的产品目标、输入和输出
2. 更新 `docs/task_goal.md` 与 `docs/implementation_plan.md`
3. 设计首批 `src/` 模块和对应 `tests/`
4. 添加真实运行命令和自动化测试命令

## 14. 给新对话 AI 的继续提示词

```markdown
我正在继续这个 `DayAvg` 项目。
请先阅读 `docs/project_memory.md`、`docs/task_goal.md` 和 `docs/implementation_plan.md`，
基于现有结构继续开发，不要重新初始化项目。

要求：
1. 不要删除已有文档和骨架结构。
2. 如果要开始写业务代码，先更新 `docs/task_goal.md` 和 `docs/implementation_plan.md`。
3. 每次有实质性变更后，更新：
   - `docs/project_memory.md`
   - `docs/progress_log.md`
   - `docs/usage.md`
4. 新生成结果继续放在 `outputs/`。
5. 如果要运行 Python，先确认可用解释器路径，因为当前环境里直接调用 `python.exe` 失败。
```
