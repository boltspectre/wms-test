# WMS 测试项目 · AI 协作分析文档（交接用）

> **用途**：本文件供**其他 AI 助手**快速接管本项目。目标是让你用最少时间定位代码、理解业务，并直接动手修改。
> 全文用 **✅ 必读 / ⏭️ 可跳过** 标注优先级。请按顺序读「必读」部分，直接跳过「可跳过」的内容。

---

## 0. 一句话定位
简化版**仓库管理系统（WMS）**候选人测试项目：在已有「商品 / 仓库 / 库位」基础 CRUD 之上，补全**入库、库存查询**，并修复预埋 Bug。业务需求见 `TASKS.md`。

---

## 1. ⚠️ 执行流程（接手 AI 必读，严格按顺序）

### 第一步：创建虚拟环境 + 启动前后端（做完即停）
你（接手 AI）在**最开始**需要替用户完成环境初始化与启动。**不要跳过这步**，用户会从项目根目录自己跑程序，但环境由你先搭好：

```bash
# —— 后端：创建虚拟环境并启动 ——
cd backend-python
python -m venv .venv                                   # 用系统 python 建 venv（Windows 下即 .venv/Scripts/python.exe）
.venv/Scripts/python.exe -m pip install -U pip uv      # 装包工具 uv
.venv/Scripts/uv.exe sync --frozen                     # 按 pyproject.toml 同步依赖（FastAPI/SQLAlchemy/aiosqlite…）
.venv/Scripts/python.exe init_data.py                  # 首次/重置时写入商品/仓库/库位/库存种子数据
.venv/Scripts/python.exe -m uvicorn app.main:app --reload   # 启动，http://localhost:8000 ，文档 /docs
# 等价写法：.venv/Scripts/python.exe app/main.py

# —— 前端：安装依赖并启动 ——
cd frontend-vue
npm install
npm run dev                                            # http://localhost:5173 ，Vite 已把 /api 代理到 8000
```

> 验证：后端 `curl http://localhost:8000/` 应返回 JSON；前端 `curl http://localhost:5173/` 应返回 HTML；`curl http://localhost:5173/api/products?page=1&pageSize=2` 应经代理拿到商品数据。

### ⛔ 停！完成第一步后必须停止
**不要**在用户没有明确指令的情况下，擅自进行任何「修复 / 实现 / 补全」类任务（入库页、库存页、跳页 Bug、删除校验 Bug 等全部不要动）。**等待用户发话**，再进入后续步骤。

### 用户的验证节奏（为什么必须这样）
用户需要做一个「对照实验」来确认 Bug 是否真的修复：
1. **先测 broken 状态**：此时两个 Bug 都处于**未修复**状态（见第 7 节），用户会自己跑程序、复现并记录错误表现。
2. **用户下令修复**：用户确认「开始修复」后，你才能动手改代码。
3. **再测 fixed 状态**：修复完成后，用户再次测试，与第 1 步记录对比，确认修复生效。

> 因此：在你收到「开始修复」的明确指令前，只做第一步（建环境 + 启动），其余一律不动。

---

## 2. 技术栈与「生效范围」（最重要）
模板同时提供 **2 套后端 + 2 套前端，但只选其一**。本环境当前激活的是：

- **后端**：Python 3.13 + FastAPI + SQLAlchemy 2.0 + SQLite（aiosqlite）
- **前端**：Vue 3 + Element Plus + Vite
- API 前缀统一 `/api`；前端用 Vite 代理把 `/api` 转到 `http://localhost:8000`

⏭️ **可跳过（未选用，改本项目无需阅读）**：
- `backend-java/`（Spring Boot 备选，完全没动）
- `frontend-react/`（React 备选，完全没动）
- `.venv/`、`node_modules/`、`uv.lock`、`package-lock.json`（依赖/环境产物）
- 仓库根的 `SOUL.md / IDENTITY.md / USER.md / BOOTSTRAP.md`（助手身份文件，与项目无关）

---

## 3. 项目结构导航（带阅读优先级）

```
wms-test-master/
├── AI分析文档.md                 ← 你正在读的交接文档
├── TASKS.md                      ✅ 任务清单（必做/选做），改之前先读
├── README.md / AI_USAGE_GUIDE.md ⏭️ 人类向说明，AI 可略读
├── backend-python/
│   ├── app/
│   │   ├── main.py               ✅ 入口：建表、CORS、注册路由、__main__ 启动（已注入 sys.path）
│   │   ├── database.py           ✅ 引擎/会话/DB 路径（SQLite = wms.db）
│   │   ├── models.py             ✅✅ 数据模型与关系（核心，必读）
│   │   ├── schemas.py            ✅✅ Pydantic 请求/响应模型（改接口必看）
│   │   ├── init_data.py          ⏭️ 种子数据，了解样例用
│   │   └── routers/
│   │       ├── products.py       ✅ 商品 CRUD（含任务3 删除校验 Bug，当前未修复）
│   │       ├── warehouses.py     ✅ 仓库/库位查询（参考实现）
│   │       └── inventory.py      ✅✅ 入库单 + 库存查询（本次已实现的逻辑）
│   └── pyproject.toml            ⏭️ 依赖清单
└── frontend-vue/
    └── src/
        ├── api/client.ts         ✅ axios 实例（baseURL=/api，统一响应拦截）
        ├── api/index.ts          ✅✅ 所有 API 函数（改前端先来这）
        ├── router/index.ts       ⏭️ 路由表
        ├── App.vue               ⏭️ 布局/菜单
        └── views/
            ├── ProductsView.vue  ✅ 商品页（含任务3 前端跳页 Bug，当前未修复）
            ├── InboundView.vue   ⚠️ 入库页【仍是 stub，待实现】
            └── InventoryView.vue ⚠️ 库存页【仍是 stub，待实现】
```

---

## 4. 数据模型与关系（✅✅ 核心必读）
库 = SQLite，表由 `models.py` 的 ORM 定义，`main.py` 启动时 `create_all` 自动建。

| 表 | 关键字段 | 关系 / 约束 |
|----|---------|------------|
| products | id, name, sku(UNIQUE), unit | 被 inventory / 入库明细 / 出库明细引用 |
| warehouses | id, code(UNIQUE), name | 1—N locations |
| locations | id, warehouse_id(FK), code(UNIQUE), status | 属某仓库；`code` 被 `inventory.location_code` 引用 |
| inventory | id, product_id(FK), location_code(FK→locations.code), quantity | **UNIQUE(product_id, location_code)**：「某商品在某库位」的库存 |
| inbound_orders | id, order_no(UNIQUE), supplier_name, status | 1—N inbound_order_items |
| inbound_order_items | id, order_id(FK), product_id(FK), quantity, location_code | 入库明细 |
| outbound_orders / outbound_order_items | 同构 | 选做 A 用，当前未实现 |

**关键认知**：
- 库存维度是 **(product_id, location_code)**，不是按仓库。
- `inventory.location_code` 直接引用 `locations.code`（字符串外键），不是 location id。
- products 删除应受库存约束（见第 7 节，当前 Bug 未处理）。

---

## 5. 已实现 / 待实现的业务逻辑
### 5.1 入库单创建 `POST /api/inbound-orders`（`inventory.py`，已实现）
- **事务**：同一函数内 `db.add` 主表 → `flush()` 拿 id → 循环加明细 + 累加/新建 inventory → `db.commit()`；`IntegrityError` 外层重试（单号唯一冲突，最多 5 次）。
- **单号**：`IN-YYYYMMDD-XXX`，XXX = 当日已存在单数 +1（三位补零）。
- **校验**：每项商品必须存在、库位必须存在、quantity>0，否则 400。
- **库存累加**：同 (product, location) 已存在则 `+=` 数量，否则新建。

### 5.2 入库单列表 / 详情 `GET /api/inbound-orders`、`GET /api/inbound-orders/{id}`（`inventory.py`，已实现）
- 列表分页；创建/详情响应含 `items[]`（带 productName）。

### 5.3 库存查询 `GET /api/inventory`（`inventory.py`，已实现）
- 参数：`keyword`(商品名/SKU 模糊)、`warehouseId`、`page`、`pageSize`(≤100)。
- 实现：`inventory JOIN product JOIN location JOIN warehouse`，按 keyword / `location.warehouse_id` 过滤，分页返回 `{list,total,page,pageSize}`。
- 返回字段：`productId, productName, sku, locationCode, warehouseName, quantity, updatedAt`。

### 5.4 商品删除 `DELETE /api/products/{id}`（`products.py`，⚠️ 当前为 Bug 状态）
- **当前未修复**：删除前**不**校验关联库存，会留下孤立库存数据。修复方式见第 7 节。**不要把它当成已实现功能。**

---

## 6. 前后端约定（✅ 改代码必须遵守，否则前后端不通）
- **统一响应**：`{code:int, message:str, data:Any}`。成功 code=200/201；分页 data=`{list,total,page,pageSize}`。
- **错误响应**：`{code:400, message:"...", data:null}`（HTTP 状态码同步对应）。
- **URL**：全部 `/api/...`；前端 `api/index.ts` 已封装各函数，新增接口请在此追加并导出。
- **前端调用风格**：`api.get(...)` 返回 axios 响应，业务 data 取 `res.data`（参考 `ProductsView.vue`）。

---

## 7. 已知 Bug（⚠️ 当前均未修复，broken 状态，先测试复现）
任务 3 预埋 2 个 Bug。**当前代码两个都处于「未修复」状态**，正是用户要先用 broken 状态测试对照用的。

1. ⚠️ **后端（未修复）**：`products.py` 的 `delete_product` 不校验关联库存 → 删除有库存的商品后会留下孤立库存。
   - **修复方式**（等用户下令后再做）：删除前 `COUNT` inventory 中该 `product_id`，>0 则 400 拒绝，避免孤立库存。

2. ⚠️ **前端（未修复）**：`ProductsView.vue` 的 `handleSubmit` 写死 `currentPage.value = 1`，导致**编辑商品后返回列表跳回第 1 页**。
   - **修复方式**（等用户下令后再做）：仅「新增」时回第 1 页，编辑时保留当前页（把 `currentPage.value = 1` 移入 `if (!form.value.id)` 分支）。

---

## 8. 待办 / 未完成（告诉其他 AI 去哪改，且需等用户指令）
- ⚠️ `frontend-vue/src/views/InboundView.vue`：入库表单全空（需商品下拉、仓库→库位级联、数量、多行增删、提交）。API `createInboundOrder` 已就绪。
- ⚠️ `frontend-vue/src/views/InventoryView.vue`：库存列表空（需搜索栏、表格、<10 红色高亮、分页、防抖）。API `getInventory` 已就绪；仓库下拉用 `getWarehouses`。
- ⚠️ `ProductsView.vue` 跳页 Bug（见第 7 节）。
- 选做 A：出库单 + 并发安全（模型已建，接口/前端未写）。
- 选做 B：单元测试（pytest 已配置，含 pytest-asyncio）。
- 选做 C：前端性能（防抖 / 虚拟滚动）。

---

## 9. 给其他 AI 的阅读 Checklist（按顺序）
1. ✅ `TASKS.md` —— 明确要做什么。
2. ✅ `backend-python/app/models.py` + `schemas.py` —— 数据模型与接口契约。
3. ✅ `backend-python/app/routers/inventory.py` —— 本次核心逻辑（入库/库存，已实现）。
4. ✅ `backend-python/app/routers/products.py` —— 删除校验 Bug（当前未修复，待修）。
5. ✅ `frontend-vue/src/api/index.ts` —— 前端如何调后端。
6. ⚠️ 改前端页面：`InboundView` / `InventoryView` / `ProductsView`（均需等用户指令）。
7. ⏭️ 跳过：`backend-java`、`frontend-react`、所有 lock / venv / node_modules、身份文件。

---

## 10. 坑 & 注意事项
- SQLite **不支持**真正的 `SELECT ... FOR UPDATE` 行锁；并发扣减（选做 A）需另选方案（`BEGIN IMMEDIATE` / 应用层乐观锁 / 唯一约束重试）。
- `database.py` 的 `echo=True` 会打印全部 SQL，提交前可关。
- 前端 `vite.config.ts` 已配 `/api` 代理到 8000；访问前端用 `http://localhost:5173`（curl 用 `127.0.0.1` 可能不通，因为绑定 localhost）。
- 删除商品被库存拦截是**修复后的预期行为**，但在当前（未修复）代码里不会发生——这是第 7 节 Bug #1 的表现。
- `app/main.py` 顶部已注入 `sys.path`，所以 `python app/main.py` 能直接跑（无需担心 `No module named 'app'`）。
