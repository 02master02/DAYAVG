# 项目记忆文档

## 1. 项目一句话概述

`DayAvg` 是一个基于 Flask 的局域网网页应用，用于计算物品从购买日至今的日均持有成本，并以仪表盘风格展示统计、历史记录、分类图标、退役状态和本地持久化能力。

## 2. 用户原始目标

用户想要一个 Python 应用，带前端页面，可在局域网访问；输入物品价格和购买时间后，计算“从购买时间到现在每天的价格”。

## 3. 当前任务目标

当前已完成 DayAvg V1.5：在保留新增、修改、图标分类和退役能力的基础上，补上 `localStorage` 快照持久化，以及 JSON 导入导出。

## 4. 当前项目状态

### 已完成

- 使用 `Flask + Jinja2 + SQLite` 实现网页应用
- 提供首页录入表单、最近计算结果和资产卡片列表
- 支持字段：`item_name`、`price`、`purchase_date`
- 支持修改已有记录的价格和购买日期
- 支持将物品标记为“已退役”或“恢复使用”
- 支持手动设置 `retired_on` 和 `retired_note`
- 正常物品按今天实时更新持有天数与日均值
- 退役物品冻结在退役日期
- 提供汇总指标：
  - 总物品价值
  - 总日均
  - 物品总数
  - 使用中数量
  - 已退役数量
  - 每件均价
- 使用用户提供的 PNG 图标资源
- 支持导出当前资产为 JSON
- 支持导入已导出的 JSON 并恢复列表
- 页面会把当前资产快照同步保存到 `localStorage`
- 自动化测试已完成并通过

### 未完成

- 删除历史记录
- 图表展示
- 登录或权限控制
- 真正可交互的筛选和排序
- 修改物品名称
- 手动指定分类

### 当前可运行程度

项目已可运行。启动后可在本机浏览器访问，也可在同一局域网下通过本机 IP 访问。

## 5. 重要文件与目录

| 路径 | 作用 | 当前状态 |
|---|---|---|
| `src/app.py` | Flask 入口、路由、页面上下文组装、导入导出、编辑与退役流程 | 已完成 |
| `src/dayavg/config.py` | 默认配置与测试日期覆盖 | 已完成 |
| `src/dayavg/services/calculator.py` | 动态时间计算、金额换算、状态求值 | 已完成 |
| `src/dayavg/services/presentation.py` | 汇总指标、图标映射和分类回退逻辑 | 已完成 |
| `src/dayavg/services/validation.py` | 新增、修改、退役设置表单校验 | 已完成 |
| `src/dayavg/services/persistence.py` | JSON 导出结构和导入校验逻辑 | 已完成 |
| `src/dayavg/storage/repository.py` | SQLite 初始化、插入、查询、更新和整批替换导入 | 已完成 |
| `templates/index.html` | 首页仪表盘模板、编辑表单、退役表单、导入导出入口 | 已完成 |
| `static/styles.css` | 页面样式与导入导出按钮样式 | 已完成 |
| `static/persistence.js` | `localStorage` 快照同步与前端导入校验 | 已完成 |
| `static/icons/` | 真实 PNG 图标资源 | 已完成 |
| `tests/test_services.py` | 服务层测试 | 已完成 |
| `tests/test_app.py` | Web 层测试 | 已完成 |
| `outputs/dayavg.db` | 本地 SQLite 数据文件 | 运行后生成 |

## 6. 输入与输出约定

### 输入

- `item_name`：文本，新增时必填
- `price`：正数，最多两位小数，新增和修改时必填
- `purchase_date`：`YYYY-MM-DD`，不能晚于今天；退役物品修改时不能晚于退役日期
- `retired_on`：`YYYY-MM-DD`，不能早于购买日期，不能晚于今天
- `retired_note`：可选文本，最长 200 字
- `import_file`：UTF-8 编码 JSON 文件，结构必须符合导出格式

### 输出

- 页面展示：
  - 总物品价值
  - 总日均
  - 每件均价
  - 使用中数量 / 已退役数量
  - 每个条目的总价、日均、购买日期、持有天数、真实图标、退役状态和退役备注
- 数据存储：
  - SQLite 文件位于 `outputs/dayavg.db`
  - 浏览器端快照存储在 `localStorage["dayavg.assetSnapshot.v1"]`
  - 导出文件为 JSON，包含稳定字段和资产数组

## 7. 核心设计思路

1. 使用服务端渲染，避免前后端分离带来的额外复杂度
2. 将 Web 层、计算层、展示层、存储层拆开，便于继续迭代
3. 用整数“分”存储金额，避免浮点误差
4. 保持单页体验，在资产卡片内展开编辑表单和退役设置表单
5. 通过“参考日期”控制状态：
   - 使用中：参考日期是今天
   - 已退役：参考日期是 `retired_on`
6. 当前真实数据源仍然是 SQLite，`localStorage` 作为浏览器侧快照镜像
7. 导入采用“校验通过后整批替换”策略，避免半成功状态

## 8. 已做过的重要决策

| 决策 | 原因 |
|---|---|
| 采用 Flask 而不是前后端分离 | 更适合这个局域网小应用的快速落地 |
| 使用 SQLite 本地文件保存历史 | 无需外部服务，部署简单 |
| 当前只允许修改价格和日期 | 与用户当前需求保持一致，避免扩大编辑范围 |
| 图标改用用户提供的 PNG | 视觉更统一，也更符合用户预期 |
| 没有专属图标时先判办公用品，再判生活用品，最后其他 | 这是用户明确指定的回退逻辑 |
| 用 `retired_on` 而不是布尔值表示退役 | 退役后需要冻结到具体日期 |
| 新增 `retired_note` 字段 | 允许记录退役原因或说明，且不影响计算逻辑 |
| 当前仓库不引入 `package.json` | 现有项目是 Flask 应用，不需要前端构建链 |
| 导出 JSON 只保留稳定字段，导入时重新计算动态值 | 避免把过期的 held_days / daily_cost 当作可信源 |

## 9. 已踩过的坑和注意事项

- 沙箱内直接导入 Flask 时会碰到 Windows `_ctypes` 访问限制，这不是业务代码错误
- SQLite 的 `Connection` 上下文管理器不会自动关闭连接，必须显式 `closing(...)`
- `sqlite_sequence` 在当前环境不适合用 `ON CONFLICT` 更新，导入后改为先删后插更稳
- 物品分类目前基于名称关键词启发式判断，不是严格分类系统
- 导入失败时必须在写库前报错，否则会污染现有数据

## 10. 当前运行命令

```powershell
D:\Anaconda\python.exe -m pip install -r requirements.txt
D:\Anaconda\python.exe src/app.py
```

## 11. 当前测试命令

```powershell
D:\Anaconda\python.exe -m unittest discover -s tests -v
```

当前结果：31 个测试全部通过。

## 12. 当前依赖

```text
Flask>=3.0,<4.0
```

## 13. 下一步任务

1. 浏览器手工验证 `localStorage["dayavg.assetSnapshot.v1"]` 是否按预期更新
2. 手工验证“导出后再导入”的完整恢复流程
3. 如果需要更完整管理，可增加删除功能
4. 如果希望更细致控制，可新增手动分类和筛选排序

## 14. 给新对话 AI 的继续提示词

```markdown
我正在继续 `DayAvg` 项目。请先阅读：
- `docs/project_memory.md`
- `docs/task_goal.md`
- `docs/implementation_plan.md`
- `docs/usage.md`

当前项目已经完成 DayAvg V1.5，支持新增、查看、修改价格 / 购买日期、真实 PNG 图标自动分类、退役日期、退役备注、localStorage 快照持久化，以及 JSON 导入导出。

请继续遵守这些规则：
1. 不要推翻现有的 Flask + SQLite 结构。
2. 先更新文档，再改代码。
3. 每次有实质性变更后，同步更新：
   - `docs/project_memory.md`
   - `docs/progress_log.md`
   - `docs/usage.md`
4. 现有模块职责：
   - Web 层：`src/app.py`
   - 计算 / 校验层：`src/dayavg/services/calculator.py`、`validation.py`
   - 展示层：`src/dayavg/services/presentation.py`
   - 持久化传输层：`src/dayavg/services/persistence.py`
   - 存储层：`src/dayavg/storage/`
5. 当前时间逻辑：
   - 使用中物品按今天实时更新
   - 退役物品按 `retired_on` 冻结
6. 当前本地持久化逻辑：
   - SQLite 是真实数据源
   - `localStorage["dayavg.assetSnapshot.v1"]` 保存浏览器快照
7. 运行测试使用：
   - `D:\Anaconda\python.exe -m unittest discover -s tests -v`
```
