# 实现计划（WMS 测试项目）

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

### 功能三 Bug 修复（后端⑤ + 前端⑥）— 待做
- 后端：`products.py` 删除商品前校验关联库存，有则 400 拒绝（避免孤立库存）。
- 前端：`ProductsView.vue` 编辑后页码跳回第 1 页 → 把 `currentPage=1` 移入「新增」分支，编辑时保留当前页。
- 前端本身有无问题先核对；若编辑跳页是唯一问题则仅改这一处。

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
功能一（✅）→ 功能二（✅）→ 功能三 →（功能四 / 选做 B / 选做 C）→ 收尾
