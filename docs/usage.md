# 使用说明

## 当前阶段

当前仓库实现的是 DayAvg V1.5：一个可在局域网访问的网页应用，用于计算物品的日均持有成本、保存历史、展示分类图标，并支持退役管理、本地快照持久化以及 JSON 导入导出。

## 技术栈说明

- 后端：`Flask`
- 模板：`Jinja2`
- 存储：`SQLite`
- 前端：原生 HTML、CSS、JavaScript
- 依赖管理：`requirements.txt`

当前项目没有 `package.json`，因此没有 `npm run lint` 或 `npm run build` 可执行。

## 安装依赖

```powershell
D:\Anaconda\python.exe -m pip install -r requirements.txt
```

## 运行程序

```powershell
D:\Anaconda\python.exe src/app.py
```

启动后默认可访问：

- `http://127.0.0.1:5000`
- `http://0.0.0.0:5000`

如果要让同一局域网下的手机或其他设备访问，请使用这台电脑的局域网 IP，例如：

```text
http://192.168.1.10:5000
```

## 页面说明

首页包含这些区域：

- 统计总览：总物品价值、总日均、物品总数、使用中数量、已退役数量、每件均价
- 新增表单：输入物品名称、购买价格、购买日期
- 资产列表：显示每条记录的图标、总价、日均、购买日期、持有天数、状态、修改入口和退役入口
- 数据工具：导出 JSON、选择 JSON 文件并导入

## 数据持久化说明

当前版本同时保留两层持久化：

- 服务端：资产数据保存到 `outputs/dayavg.db`
- 浏览器端：页面加载后把当前资产快照同步写入 `localStorage`

自动同步时机：

- 新增资产后
- 修改资产后
- 设置退役或恢复使用后
- 导入 JSON 成功后
- 页面刷新后重新渲染时

浏览器端使用的 `localStorage` key 为：

```text
dayavg.assetSnapshot.v1
```

## 导出与导入

### 导出 JSON

点击“导出 JSON”按钮后，浏览器会下载当前完整资产数据。

导出文件内容包含：

- `schema_version`
- `items`
- 每条资产的 `id`
- `item_name`
- `price_cents`
- `purchase_date`
- `created_at`
- `retired_on`
- `retired_note`

### 导入 JSON

使用方式：

1. 点击“选择 JSON”
2. 选择之前导出的 JSON 文件
3. 点击“导入 JSON”

导入保护分两层：

- 前端先做基础结构校验
- 服务端再做严格校验并在通过后整批替换当前列表

如果导入失败，现有资产数据不会被覆盖。

## 退役规则

- 正常物品：每天按“今天”实时更新持有天数和日均持有成本
- 已退役物品：冻结在你设置的退役日期，不再随着时间继续变化
- 退役备注：只用于展示说明，不参与计算
- 恢复使用：会清空退役日期和退役备注，并重新按今天动态更新

## 图标分类说明

当前版本优先匹配这些专属图标：

- 手机
- 电脑
- 平板
- 手环手表
- 车子
- 鞋子
- 衣服

如果没有命中专属类目，则按下面顺序回退：

1. 办公用品
2. 生活用品
3. 其他

## 数据保存位置

- 历史数据：`outputs/dayavg.db`
- 图标资源：`static/icons/`
- 本地持久化脚本：`static/persistence.js`

## 实际检查命令

因为当前项目没有 `package.json`，本轮没有运行 `npm run lint` 或 `npm run build`。

实际运行的检查命令是：

```powershell
D:\Anaconda\python.exe -m unittest discover -s tests -v
```

结果：`31` 个测试全部通过。

## 常见问题

### 刷新页面后为什么资产还在？

因为当前项目同时使用了 SQLite 和 `localStorage`。SQLite 负责服务端保存，`localStorage` 负责浏览器端快照备份。

### 导入错误 JSON 会不会把现有数据覆盖掉？

不会。只有在前端基础校验和服务端严格校验都通过后，系统才会替换当前资产列表。

### 导出后再导入能恢复列表吗？

可以。当前导出格式就是当前版本支持的导入格式。
