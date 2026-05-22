# 开发记录

## 2026-05-21 17:05

### 已完成

- 将项目目标从“工作流初始化”升级为 DayAvg V1 应用实现
- 实现 Flask 首页、提交路由和服务端渲染页面
- 实现输入校验、持有天数计算、金额格式化和 SQLite 持久化
- 实现局域网可访问的前端页面与历史记录展示
- 编写服务层与 Web 层自动化测试
- 修复 SQLite 连接未关闭导致的 Windows 文件锁问题

## 2026-05-21 17:40

### 已完成

- 将首页改版为移动端资产仪表盘风格
- 新增总物品价值、总日均、每件均价、最高日均、最低日均等汇总指标
- 为条目增加基于名称关键词的图标和分类标签
- 将整体配色调整为更偏学术感的蓝灰、米白和低饱和辅助色

## 2026-05-21 18:10

### 已完成

- 为已有物品新增“修改”入口
- 支持在资产卡片内直接修改价格和购买日期
- 增加 SQLite 更新方法，并在修改后重新计算持有天数和日均持有成本

## 2026-05-21 18:35

### 已完成

- 把用户提供的 10 个 PNG 图标复制到 `static/icons/`
- 用真实图片图标替换原有内联 SVG
- 重写分类逻辑：专属类优先，其次办公用品、生活用品，最后其他

## 2026-05-21 19:05

### 已完成

- 新增“已退役”状态与退役日期存储
- 修复时间逻辑：正常物品按今天实时更新，退役物品按退役日期冻结
- 增加“标记退役 / 恢复使用”路由与按钮
- 允许退役物品在编辑价格和购买日期时继续以退役日期为冻结边界
- 为退役功能补充自动化测试和测试日期覆盖能力

## 2026-05-21 20:15

### 已完成

- 新增退役设置表单，支持手动设置退役日期
- 新增退役备注字段，支持记录退役原因或说明
- 为旧数据库增加 `retired_note` 兼容迁移逻辑
- 在资产卡片中增加“退役设置 / 调整退役”入口
- 恢复使用时同步清空退役日期和退役备注

## 2026-05-21 21:00

### 已完成

- 确认当前项目技术栈为 `Flask + Jinja2 + SQLite`，且仓库不存在 `package.json`
- 新增 `src/dayavg/services/persistence.py`，统一处理导出结构和导入 JSON 校验
- 为仓库存储层增加整批替换能力，用于导入恢复资产列表
- 新增 `GET /items/export` 和 `POST /items/import`
- 新增 `static/persistence.js`，在页面加载后自动把当前资产快照同步到 `localStorage`
- 新增导出 JSON 与导入 JSON 的轻量入口，保持当前页面布局基本不变
- 增加前端基础校验和服务端严格校验，防止错误 JSON 覆盖现有资产
- 重写入口模板和测试，覆盖导入导出与快照注入流程

### 修改文件

- `docs/task_goal.md`
- `docs/implementation_plan.md`
- `docs/progress_log.md`
- `docs/project_memory.md`
- `docs/usage.md`
- `src/app.py`
- `src/dayavg/services/persistence.py`
- `src/dayavg/storage/repository.py`
- `templates/index.html`
- `static/styles.css`
- `static/persistence.js`
- `tests/test_app.py`
- `tests/test_services.py`

### 当前结果

DayAvg 现在支持：

- 页面刷新后由 SQLite 保持资产列表不丢失
- 浏览器端把当前资产列表快照同步保存到 `localStorage`
- 新增、修改、退役、恢复和导入成功后自动更新本地快照
- 导出当前资产为 JSON
- 导入此前导出的 JSON 并恢复列表
- 错误 JSON 被前后端双重校验拦截，不会破坏现有数据

### 测试与验证

- 已运行：`D:\Anaconda\python.exe -m unittest discover -s tests -v`
- 结果：`31` 个测试全部通过
- 说明：当前项目没有 `package.json`，因此没有 `npm run lint` 或 `npm run build`

### 下一步

1. 在浏览器里手动走一遍“新增 -> 导出 -> 清空/替换 -> 导入恢复”的完整流程
2. 如果还想继续完善资产管理，可以增加删除功能
3. 如果想提升可控性，可以继续增加筛选、排序或手动分类
