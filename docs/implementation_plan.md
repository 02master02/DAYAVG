# 实现计划

## 总体思路

保持现有 Flask 服务端渲染结构不变，在此基础上补一层轻量持久化能力：

1. 服务端提供稳定的 JSON 导出与导入接口
2. 浏览器端在页面加载后把当前资产快照同步到 `localStorage`
3. 新增、修改、退役、恢复或导入成功后，刷新后的页面会自动重新写入最新快照
4. 导入前在前端先做基础结构校验，导入时在服务端再做严格校验

## 模块拆分

| 文件 | 职责 | 状态 |
|---|---|---|
| `src/app.py` | 新增导入导出路由，向模板注入资产快照 | completed |
| `src/dayavg/services/persistence.py` | 导出结构生成、导入 JSON 校验与解析 | completed |
| `src/dayavg/storage/repository.py` | 支持整批替换资产数据以完成导入恢复 | completed |
| `templates/index.html` | 增加最小化的导出/导入入口和本地快照脚本挂载点 | completed |
| `static/styles.css` | 为导入导出操作增加少量按钮样式 | completed |
| `static/persistence.js` | 负责 localStorage 同步、导入前校验和文件提交 | completed |
| `tests/test_services.py` | JSON 结构校验与导入解析测试 | completed |
| `tests/test_app.py` | 导入导出路由、失败保护与页面快照注入测试 | completed |

## 执行步骤

1. 新增数据传输服务模块，定义统一导出格式
2. 为仓库存储层增加整批替换写入能力
3. 在 Flask 中添加 `GET /items/export` 和 `POST /items/import`
4. 在模板中加入导出按钮、导入按钮和隐藏文件输入
5. 新增原生 JS，把服务端资产快照同步到 `localStorage`
6. 前端先做基础 JSON 校验，服务端再做严格校验
7. 补充自动化测试并运行
8. 更新使用说明、进度记录和项目记忆

## 风险点

- 导入逻辑如果直接写库，失败时可能污染现有数据，必须做完整校验后再替换
- `localStorage` 在隐私模式或容量限制下可能写入失败，前端要静默兜底
- 导入导出入口需要尽量轻量，避免破坏当前卡片式页面布局
- 当前项目没有 `package.json`，所以不能伪造前端 lint/build 命令

## 测试计划

| 测试 | 命令 | 预期结果 |
|---|---|---|
| 服务层测试 | `D:\Anaconda\python.exe -m unittest tests.test_services -v` | JSON 校验、导入解析通过 |
| Web 集成测试 | `D:\Anaconda\python.exe -m unittest tests.test_app -v` | 导出、导入、失败保护和页面快照注入通过 |
| 全量测试 | `D:\Anaconda\python.exe -m unittest discover -s tests -v` | 所有测试通过 |
| 手工运行 | `D:\Anaconda\python.exe src/app.py` | 可导出 JSON、导入 JSON、刷新后列表仍存在 |
