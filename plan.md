# 实现计划（WMS 测试项目）

> 流程：逐个修改，每改完一项我汇报改动，你检查无误后说「继续」，我再改下一项。
> 依据：`TASKS.md`、`AI分析文档.md`、`docs/API_SPEC.md`、源码现状。
> 技术栈：后端 Python 3.12 + FastAPI + SQLAlchemy 2.0 + SQLite；前端 Vue3 + Element Plus + Vite。

---

## 重要更正
`AI分析文档.md` 称后端 `inventory.py` 的入库单/库存查询「已实现」，但**实际为 stub（`raise 501`）**。
因此后端这两个接口**必须实现**，不只是补前端页面。本计划据此修正。

---

## 改动清单（按点编号，依次执行）

### ① 后端·入库单创建 API —— `backend-python/app/routers/inventory.py`
- 实现 `POST /api/inbound-orders`：
  - 生成入库单号 `IN-YYYYMMDD-XXX`（XXX = 当日已存在单数 +1，三位补零；单号唯一冲突最多重试 5 次）。
  - 校验：每项 `product_id` 必须存在、`location_code` 必须存在、`quantity>0`（schema 已约束），否则返回 400。
  - **数据库事务**：在同一会话内 `add` 入库单 → `flush()` 拿 id → 循环加明细 + 累加/新建 `inventory` → 全部成功才 `commit()`；任何校验失败或异常 `rollback()`。
  - 库存累加：相同 `(product_id, location_code)` 已存在则 `+=`，否则新建。
  - 响应：201 + `{code:201, message:"入库单创建成功", data:{id,orderNo,supplierName,status:"COMPLETED",items:[{productId,productName,quantity,locationCode}],createdAt}}`。
- 验收：用 curl 调 `/api/inbound-orders` 创建成功；库存表对应数量增加；缺商品/库位时返回 400。

### ② 前端·入库单页面 —— `frontend-vue/src/views/InboundView.vue`
- 明细行：商品下拉（搜索，调 `getProducts`）、仓库下拉（`getWarehouses`）→ 库位级联（`getLocations`）、数量输入。
- 支持「添加/删除」明细行（已有 `addItem/removeItem` 骨架，补全字段绑定与级联逻辑）。
- 提交：`handleSubmit` 调 `createInboundOrder`，成功后 `ElMessage` 提示并重置表单。
- 校验：供应商名称非空、每行商品/库位/数量必填。
- 验收：浏览器操作可成功创建入库单；成功后库存查询页能看到新增库存。

### ③ 后端·库存查询 API —— `backend-python/app/routers/inventory.py`
- 实现 `GET /api/inventory`：
  - 参数 `keyword`（商品名/SKU 模糊）、`warehouseId`、`page`、`pageSize(≤100)`。
  - JOIN `inventory × product × location × warehouse`，按 keyword / `location.warehouse_id` 过滤，分页。
  - 返回 `{list:[{productId,productName,sku,locationCode,warehouseName,quantity,updatedAt}], total, page, pageSize}`。
  - 性能：对 `inventory.product_id`、`location_code` 利用唯一约束；COUNT 与分页用同一过滤条件。
- 验收：curl 带 keyword/warehouseId 返回正确分页数据。

### ④ 前端·库存查询页面 —— `frontend-vue/src/views/InventoryView.vue`
- 搜索栏：商品名称/SKU 模糊输入 + 仓库下拉（`getWarehouses`）+ 查询按钮；输入**防抖**（300ms）。
- 表格：商品名称、SKU、库位编码、仓库、库存数量、更新时间；**数量 < 10 的行红色高亮**（`getRowStyle`）。
- 分页：后端分页，page 变化时重新请求；total 来自接口。
- 挂载即加载首屏数据。
- 验收：页面能搜索、分页、低库存红色高亮。

### ⑤ Bug 修复·后端删除校验 —— `backend-python/app/routers/products.py`
- `delete_product`：删除前 `COUNT` `inventory` 中该 `product_id`，若 `>0` 返回 400 拒绝，避免孤立库存。
- 验收：对「有库存」的商品调用删除返回 400；无库存则成功。

### ⑥ Bug 修复·前端编辑跳页 —— `frontend-vue/src/views/ProductsView.vue`
- `handleSubmit` 中把 `currentPage.value = 1` 移入「新增」分支（`if (!form.value.id)`）；编辑时保留当前页码。
- 验收：翻到第 2 页后编辑某条商品，返回列表仍停留在第 2 页。

### ⑦ 选做 A·出库单 + 并发安全
- 模型：`models.py` 增加 `OutboundOrder` / `OutboundOrderItem`（表已存在于 API_SPEC）。
- 后端：`POST /api/outbound-orders`，扣减前检查库存充足；并发安全方案（SQLite 无行锁）：用 `BEGIN IMMEDIATE` / 应用层乐观锁 / 唯一约束重试，在 `NOTES.md` 说明选型理由。
- 前端：新增出库页面（路由/菜单按需补充）。
- 验收：正常出库扣减库存；并发下不超卖。

### ⑧ 选做 B·单元测试（pytest）
- 后端：入库单创建 Service 层（含事务/校验）至少 2 用例。
- 前端：库存列表筛选逻辑至少 1 用例。

### ⑨ 选做 C·前端性能优化
- 在 ④ 基础上强化：虚拟滚动（大数据量 500+ 不卡顿）、防抖（已含）、后端分页（已含）。

### ⑩ 收尾·`NOTES.md` + 提交规范
- 根目录写 `NOTES.md`：AI 使用说明 + Bug 发现与修复方式 + 选做方案说明。
- 确认提交检查清单：必做功能正常、可一键启动、无明显报错、Git 提交清晰。

---

## 执行顺序
① → ② → ③ → ④ → ⑤ → ⑥ →（⑦ ⑧ ⑨ 选做）→ ⑩
当前仅执行 **①**，其余待你确认后逐项推进。
