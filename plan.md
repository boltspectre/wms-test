# 实现计划（WMS 测试项目）

> **协作方式（人指挥、AI 执行）**：本项目由你（人工）给出方向——**按功能归类、前后端一起做、改完你确认「继续」再做下一个**；我（AI）负责读代码、列计划、写代码、起服务、做测试。每个功能实现后暂停等待你确认，再进入下一个。
> 流程：以**完整功能**为单位推进。同一功能的前后端一起改（若该功能纯后端、无前端则只改后端）；前端本身无问题则不改动。
> 每完成一个功能，汇报改动 + **【网页操作步骤 + 正确预期结果】**（不仅是 curl/API 测试），你确认「继续」后再做下一个功能。
> 依据：`TASKS.md`、`AI分析文档.md`、`docs/API_SPEC.md`、源码现状。
> 技术栈：后端 Python 3.12 + FastAPI + SQLAlchemy 2.0 + SQLite；前端 Vue3 + Element Plus + Vite。

---

## 重要更正
`AI分析文档.md` 称后端 `inventory.py` 的入库单/库存查询「已实现」，但**实际为 stub（`raise 501`）**。因此后端这两个接口**必须实现**，不只是补前端页面。本计划据此修正。

---

## 改动清单（按完整功能分组）

### 功能一 入库单（后端① + 前端②）— 已完成 ✅
- 后端：`POST /api/inbound-orders`（单号 `IN-YYYYMMDD-XXX`、事务、库存累加、缺商品/库位→400）。见 `backend-python/app/routers/inventory.py`。
- 前端：`InboundView.vue`（商品远程搜索、仓库→库位级联、多行明细、提交校验）。见 `frontend-vue/src/views/InboundView.vue`。
- 契约：后端 schemas 用 Pydantic alias 兼容前端 camelCase，不改前端。

### 功能二 库存查询（后端③ + 前端④）— 已完成 ✅
- 后端：`GET /api/inventory`（keyword/warehouseId 过滤、JOIN 四表、分页、camelCase 兼容）。见 `inventory.py` 的 `query_inventory`。
- 前端：`InventoryView.vue`（搜索栏+仓库下拉、低库存<10 红色高亮、后端分页、输入防抖 300ms）。见 `frontend-vue/src/views/InventoryView.vue`。

### 功能三 Bug 修复（后端⑤ + 前端⑥）— 已完成 ✅
- 后端：`products.py` `delete_product` 删除前查 `Inventory`，有则 `400` 拒绝（detail 含库位与数量），无库存才允许删除。见 `backend-python/app/routers/products.py`。验证：有库存商品→400、无库存临时商品→200、不存在→404；数据库保持 6 个商品。
- 前端：`ProductsView.vue` `handleSubmit` 把 `currentPage=1` 移入「新增」分支，编辑时保留当前页码；其余逻辑不动。见 `frontend-vue/src/views/ProductsView.vue`。编译通过。
- 说明：当前种子仅 6 个商品（pageSize=10，全在第 1 页），编辑跳页 Bug 在页面上不可见；需 >10 个商品（出现第 2 页）才能直观复现差异。

### 功能四 选做 A 出库单 + 并发安全（后端 + 前端）— 待做
- 模型：`OutboundOrder`/`OutboundOrderItem`（API_SPEC 已有表）。
- 后端：`POST /api/outbound-orders`（扣减前校验库存充足）；SQLite 并发安全用 `BEGIN IMMEDIATE` / 乐观锁 / 唯一约束重试。
- 前端：出库页面（路由/菜单按需补充）。

### 选做 B 单元测试（pytest）— 待做
- 入库单创建 Service 层（事务/校验）≥2 用例；库存列表筛选逻辑 ≥1 用例。

### 选做 C 前端性能 — 待做
- 在功能二基础上：虚拟滚动（500+ 不卡）、防抖（已含）、后端分页（已含）。

### 收尾 ⑩ `NOTES.md` + 提交规范 — 待做
- 根目录写 `NOTES.md`：AI 使用说明 + Bug 发现与修复方式 + 选做方案说明。
- 提交检查：必做功能正常、可一键启动、无明显报错、Git 提交清晰。

---

## 执行顺序
功能一（✅）→ 功能二（✅）→ 功能三（✅）→（功能四 / 选做 B / 选做 C）→ 收尾
