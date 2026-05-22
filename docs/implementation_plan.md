# 实现计划

## 总体思路

保持现有 Flask 服务端渲染结构不变，在此基础上补齐资产操作能力：

1. 扩展资产字段，支持名称、手动分类、资产备注和更完整的退役信息
2. 增加删除路由和页面二次确认，保证删除后指标与列表同步更新
3. 调整退役计算逻辑，使用退役日期冻结持有天数，并按实际成本重算日均
4. 保持现有导入导出和 `localStorage` 快照能力，对新增字段做兼容扩展

## 模块拆分

| 文件 | 职责 | 状态 |
|---|---|---|
| `src/app.py` | 扩展编辑、删除和退役路由，维持页面上下文 | completed |
| `src/dayavg/services/calculator.py` | 增加“实际成本”参与的退役日均计算 | completed |
| `src/dayavg/services/validation.py` | 校验新增字段、删除流程和退役卖出价格 | completed |
| `src/dayavg/services/persistence.py` | 扩展导入导出 JSON 字段并保持兼容 | completed |
| `src/dayavg/services/presentation.py` | 支持手动分类展示和图标映射 | completed |
| `src/dayavg/storage/repository.py` | 增加字段迁移、删除能力和新字段读写 | completed |
| `templates/index.html` | 补齐编辑项、删除确认和更完整的退役表单 | completed |
| `static/styles.css` | 为新增字段和删除确认补最小样式 | completed |
| `static/persistence.js` | 扩展快照校验结构 | completed |
| `tests/test_services.py` | 覆盖退役成本、校验和导入导出新字段 | completed |
| `tests/test_app.py` | 覆盖编辑、删除、退役冻结和刷新后正确性 | completed |

## 执行步骤

1. 扩展数据库字段和数据结构，加入分类、备注、退役原因和卖出价格
2. 调整表单校验与计算逻辑，确保退役资产按实际成本和退役日期计算
3. 更新 Flask 路由，补齐编辑全部字段、删除和恢复后的状态更新
4. 更新模板和最小样式，加入删除二次确认和新增表单字段
5. 扩展导入导出与本地快照校验，让新增字段可持久化
6. 补充自动化测试并运行检查命令
7. 更新使用说明、进度记录和项目记忆

## 风险点

- SQLite 旧库需要字段迁移，不能破坏已有数据
- 删除能力一旦路由或确认处理不当，容易造成误删
- 卖出价格参与退役计算后，要避免实际成本出现负数
- 导入导出结构变更后，前后端校验需要同步
- 退役表单字段增加后，仍要尽量保持当前卡片式页面布局
- 当前项目没有 `package.json`，所以不能伪造前端 lint/build 命令

## 测试计划

| 测试 | 命令 | 预期结果 |
|---|---|---|
| 服务层测试 | `D:\Anaconda\python.exe -m unittest tests.test_services -v` | 退役成本、校验和导入解析通过 |
| Web 集成测试 | `D:\Anaconda\python.exe -m unittest tests.test_app -v` | 编辑、删除、退役冻结、恢复和快照注入通过 |
| 全量测试 | `D:\Anaconda\python.exe -m unittest discover -s tests -v` | 所有测试通过 |
| 编译检查 | `D:\Anaconda\python.exe -m compileall src` | `src` 编译通过 |
| 手工运行 | `D:\Anaconda\python.exe src/app.py` | 编辑、删除、退役后刷新数据仍正确 |
