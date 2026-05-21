# 实现计划

## 总体思路

继续使用 Flask 做服务端渲染，保持局域网部署简单。当前这一轮在已有“退役”能力基础上，把“退役日期”和“退役备注”提升为正式数据字段，并在资产卡片内提供独立的退役设置表单。

## 模块拆分

| 文件 | 职责 | 状态 |
|---|---|---|
| `src/app.py` | Flask 入口、路由、页面上下文、编辑和退役流程 | completed |
| `src/dayavg/config.py` | 默认配置与测试日期覆盖 | completed |
| `src/dayavg/services/calculator.py` | 动态持有天数、日均成本和冻结逻辑 | completed |
| `src/dayavg/services/presentation.py` | 汇总指标、图标分类和页面展示字段 | completed |
| `src/dayavg/services/validation.py` | 新增、修改、退役设置表单校验 | completed |
| `src/dayavg/storage/repository.py` | SQLite 初始化、查询、修改和退役字段存储 | completed |
| `templates/index.html` | 仪表盘页面、编辑表单、退役设置表单 | completed |
| `static/styles.css` | 页面样式、状态标签、退役设置区域样式 | completed |
| `tests/test_services.py` | 计算、分类、退役设置校验测试 | completed |
| `tests/test_app.py` | 页面访问、新增、修改、退役、恢复测试 | completed |

## 执行结果

1. 已更新文档，将目标扩展到 DayAvg V1.4
2. 已为数据库兼容增加 `retired_note` 字段，并保留旧库自动迁移能力
3. 已新增退役设置表单校验，支持手动退役日期和退役备注
4. 已新增退役设置页面状态和保存逻辑
5. 已更新模板和样式，支持在资产卡中编辑退役信息
6. 已补充自动化测试并通过

## 风险点

- 旧数据库需要安全补字段，不能破坏现有历史记录
- 退役日期必须同时受购买日期和当前日期约束
- 页面上同时存在新增、修改、退役三类表单，状态隔离必须清楚

## 测试方案

| 测试 | 命令 | 结果 |
|---|---|---|
| 服务层测试 | `D:\Anaconda\python.exe -m unittest tests.test_services -v` | 通过 |
| Web 集成测试 | `D:\Anaconda\python.exe -m unittest tests.test_app -v` | 通过 |
| 全量测试 | `D:\Anaconda\python.exe -m unittest discover -s tests -v` | 通过，23 个测试全部通过 |
| 手工运行 | `D:\Anaconda\python.exe src/app.py` | 可在页面设置退役日期与备注，退役后冻结，恢复后继续更新 |
