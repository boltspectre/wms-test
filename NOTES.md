# NOTES — AI 协助说明 & 项目记录

> 本文件供协作者 / 评审快速了解：本项目如何使用 AI 完成、环境如何启动、埋了哪些 Bug 以及如何测试与提交。

---

## 一、AI 使用说明（AI_USAGE）

本项目由 AI（WorkBuddy）在**人工指令驱动**下完成，遵循「逐项修改、改完汇报、人工确认「继续」后再做下一项」的节奏，并以「完整功能为单位」前后端一起交付。

> 想了解我们**具体是怎么一步一步配合**完成这个项目的（按功能归类、前后端一起做、每步人工确认）？见 **第七节 · 协作过程记录**。这是本仓库最重要的背景说明，建议先读。

- 技术决策依据：`backend-python/AI分析文档.md`（明确后端 Python+FastAPI、前端 Vue3，Java/React 两套不选用）。
- 工作约定（已写入项目记忆）：
  - 功能以「完整功能」为单位推进，前后端一起改（除非该功能纯后端无前端）；前端本身无问题则不改动。
  - 每次完成一个功能，既在 `测试.md` 追加【修改内容 + 测试校验方法】，也在对话中直接返回同样内容。
  - 契约统一：前端 `api/index.ts` 与 `API_SPEC.md` 用 **camelCase**，后端用 snake_case，新接口用 Pydantic `alias` 兼容，不改动前端。
- 沙箱运维坑（务必记牢）：改后端代码后必须 `taskkill /F /IM python.exe` 清掉残留 uvicorn 再重启唯一干净实例，否则旧进程会返回诡异 500；`uvicorn --reload` 在沙箱内不生效；排查 500 用 `TestClient` 直连可拿到真实 traceback。

---

## 二、环境准备与启动

### 后端（Python 3.12.9 + FastAPI + SQLAlchemy 2.0 + SQLite）
```bash
cd backend-python
# 用系统 Python 3.12.9 建好的 .venv（managed 3.13/3.14 的 venv 缺 pip，不可用）
# 安装依赖（沙箱用官方 PyPI；若 pypi.org 不可达，用阿里云镜像）
.venv/Scripts/python.exe -m pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
# 或：pip install uv -> uv sync --frozen（uv.lock 已锁定）

# 初始化种子数据（生成 wms.db）
.venv/Scripts/python.exe init_data.py

# 启动（沙箱改代码后需先 taskkill 再重启）
.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# 文档：http://localhost:8000/docs
```

### 前端（Vue 3 + Element Plus + Vite）
```bash
cd frontend-vue
npm install
npm run dev   # http://localhost:5173 ，/api 代理到 8000
```

### 单元测试（选做 B）
```bash
cd backend-python
.venv/Scripts/python.exe -m pytest test_wms.py -v   # 13 用例，全通过
```

---

## 三、已实现功能清单

| 功能 | 后端 | 前端 | 状态 |
|------|------|------|------|
| 入库单（必做1） | `POST /api/inbound-orders`（单号/事务/累加库存） | `InboundView.vue` | ✅ |
| 库存查询（必做2） | `GET /api/inventory`（四表JOIN/过滤/分页） | `InventoryView.vue` | ✅ |
| Bug 修复（必做3） | `delete_product` 库存校验 | `ProductsView.vue` 编辑跳页 | ✅ |
| 出库单 + 并发（选做A） | `POST/GET /api/outbound-orders`（原子扣减） | `OutboundView.vue` | ✅ |
| 单元测试（选做B） | `test_wms.py`（13 用例） | — | ✅ |
| 前端性能（选做C） | — | `App.vue` keep-alive | ✅ |

全局：接口错误统一以**右上角 ElNotification 弹窗**提示（`frontend-vue/src/api/client.ts`）。

---

## 四、预埋 Bug 与修复记录（Bug Records）

### Bug 1 — 删除商品产生孤立库存（后端）
- **位置**：`backend-python/app/routers/products.py` 原 `delete_product`
- **现象**：直接 `db.delete(product)`，但 `Inventory.product_id` 是 FK，而 SQLite 默认**不开启 `PRAGMA foreign_keys`**，删除会"成功"却留下指向已删商品的孤立库存记录。
- **修复**：删除前先查 `Inventory`，存在关联库存则返回 `400`（含库位与数量提示），无库存才删除。前端 `ProductsView.vue` 在删除失败时由拦截器弹窗提示。

### Bug 2 — 编辑商品后列表跳回第 1 页（前端）
- **位置**：`frontend-vue/src/views/ProductsView.vue` 原 `handleSubmit`
- **现象**：提交后无条件 `currentPage.value = 1`，导致在第 2 页及以后编辑商品时列表跳回第 1 页（页码丢失）。
- **修复**：把 `currentPage.value = 1` 移入「新增」分支（`if(!form.value.id) currentPage.value = 1`），编辑时保留当前页码。
- 注：种子仅 6 个商品（pageSize=10，全在第 1 页），此 Bug 需 >10 商品（出现第 2 页）才直观复现。

### Bug 3 — 入库/库存接口原是 stub（需求文档与实现不符）
- **位置**：`backend-python/app/routers/inventory.py` 原 `create_inbound_order` / `query_inventory` 仅是 `raise 501`。
- **现象**：`AI分析文档.md` 称「已实现」，实际不可用。
- **修复**：按需求文档完整实现两个接口（见第三节）。

### Bug 4 — 契约不一致（camelCase vs snake_case）
- **现象**：前端与 `API_SPEC.md` 用 camelCase（`supplierName`/`productId`/`locationCode`/`warehouseId`/`pageSize`），后端原用 snake_case，直接调用会 422。
- **修复**：后端新增/调整 Pydantic 模型加 `alias` + `populate_by_name=True`，`Query(alias=...)` 兼容参数，不改动前端。

---

## 五、并发安全设计（出库扣减）

SQLite 不支持行级锁，出库扣减采用：
1. `PRAGMA busy_timeout = 5000`：并发写事务在锁上等待 5s，避免立即 `database is locked`。
2. 库存扣减用**单条原子 UPDATE**：
   `UPDATE inventory SET quantity = quantity - :qty WHERE product_id=:pid AND location_code=:loc AND quantity >= :qty`
   由 SQLite 写锁保证「读-判断-改」不被并发事务穿插，从根本上杜绝超卖/负库存与丢失更新。
3. 单号唯一约束冲突、锁等待超时均做**最多 5 次有限重试**；扣减 `rowcount==0`（库存不足/无库存）→ 400。

---

## 六、提交与协作约定（参考 AI_USAGE_GUIDE）

- 分支：默认 `master`，已绑定远程 `git@github.com:boltspectre/wms-test.git`（SSH）。
- 提交前：确认 `测试.md` 已记录本次变更与测试；根目录 `NOTES.md` 反映最新状态。
- 提交信息遵循仓库 `AI_USAGE_GUIDE` 规范（如 `feat: 实现出库单与并发安全` / `fix: 删除商品前校验关联库存`）。
- 注意：`.gitignore` 已忽略 `wms.db`、`.venv` 等；新增 `test_wms.py` 与 `NOTES.md`、`测试.md` 应纳入版本控制。

---

## 七、协作过程记录（我们是如何配合完成本项目的）

> 本章还原本项目的人机协作全过程，目的是让后续协作者 / 评审一眼看懂：
> **这个仓库不是「AI 一次性自动生成」的，而是在「人类指挥、AI 执行」的节奏下，按功能逐步交付的。**
> 你（用户）定方向、定红线、逐步验收；我（AI）读代码、列计划、写代码、起服务、做测试、写文档。

### 7.1 核心指令（你是怎么要求我的）

贯穿全程的几条"总纲"，由你在对话中逐步下达，我严格照办：

1. **「先读需求、配环境、起服务，但先不要改代码」** —— 早期你明确划了红线：只做环境准备，不动业务代码，等你说"开始"再写。
2. **「按功能、前后端一起完成」** —— 你要求以**完整功能**为单位推进：同一个功能的前后端一起改（除非该功能纯后端、无前端）；前端本身没问题的就不强行改动。
3. **「改完告诉我你改了什么，我检查完说『继续』你再做下一个」** —— 这是关键节奏：**human-in-the-loop**，我每完成一个功能就暂停，等你确认才进入下一个，绝不一次大改。
4. **「每次改完，把『如何测试 / 正确预期结果』带给我」** —— 你要求每个功能交付时都附上可操作的验证方法，尤其强调**网页怎么点、预期看到什么**。
5. **「写个 测试.md，每次改完追加，也直接返回给我」** —— 于是每个功能的【修改内容 + 测试校验方法】既在对话里返回，也沉淀进 `测试.md`。
6. **「错误提示要在右上角弹窗，不要只在接口里提示」** —— 你要求前端把所有接口报错统一改成右上角 `ElNotification` 弹窗，而不只是控制台日志或接口返回。
7. **「继续完成，直接完成所有的」** —— 最后你一声令下，我把剩余的 功能四（出库单+并发）、选做 B（单元测试）、选做 C（前端性能）、`NOTES.md` 一次性做完并验证。

### 7.2 实际走过的几步（时间线）

| 阶段 | 你下的指令 / 决策 | 我做的事 |
|------|------------------|----------|
| ① 绑定仓库 | 提供 SSH 地址 `git@github.com:boltspectre/wms-test.git` | clone 并绑定远程（HTTP 在沙箱不可达，改用 SSH） |
| ② 备环境 | "读需求 + AI分析文档，配环境、启动，先别改代码" | 读文档、建 venv、装依赖、初始化种子数据、起前后端，严格遵守不写代码红线 |
| ③ 列计划 | "先把要做的列出来，写个 plan.md" | 通读 `TASKS.md`/`AI分析文档.md`/`API_SPEC.md`/源码，按**完整功能**分组列出所有待改点，写入 `plan.md` 交你确认 |
| ④ 逐项实现 | "开始" → 我做完一个 → 你"继续" → 下一个 | 从功能一开始，每完成一个功能就汇报【改了什么】+【网页测试步骤与预期】，等你「继续」再做下一个；前端无误的不动 |
| ⑤ 沉淀测试 | "写个 测试.md，每次追加也直接返回" | 形成本仓库 `测试.md`：每个功能一章，含修改内容 + 后端 API + 前端网页操作 + 负向校验 |
| ⑥ 错误弹窗 | "错误要在右上角弹窗" | 改造 `frontend-vue/src/api/client.ts` 响应拦截器为全局 `ElNotification` |
| ⑦ 收尾 | "直接完成所有的" | 做完功能四 / 选做 B / 选做 C / `NOTES.md`，全部跑通验证 |

### 7.3 沉淀下来的关键约定（已写入项目记忆，后续照此执行）

- **以「完整功能」为单位**：同一功能前后端一起改；纯后端功能只改后端；前端没问题就不改。
- **human-in-the-loop**：AI 每步产出后暂停，等「继续」确认，避免擅自大改、改完不知对错。
- **契约统一**：前端与 `API_SPEC.md` 用 camelCase，后端用 snake_case，新接口用 Pydantic `alias` 兼容，**不迁就改动前端**。
- **测试即文档**：每个功能的交付物 = 代码 + 可操作的网页测试步骤 + 预期结果，沉淀进 `测试.md`。
- **沙箱运维红线**：改后端代码后必须 `taskkill /F /IM python.exe` 清掉残留 uvicorn 再重启唯一干净实例，否则旧进程会返回诡异 500（`uvicorn --reload` 在沙箱不生效）。

### 7.4 给后来者：怎么读这套文档

- **`plan.md`** —— 计划视角：按功能分组列了"要改什么"，并标注每项的完成状态。
- **`测试.md`** —— 验收视角：每个功能一章，告诉你**改了哪些文件 + 怎么在网页上点 + 预期看到什么 + 怎么 curl 验证**，照着点一遍即可验收。
- **`NOTES.md`（本文件）** —— 全貌视角：环境怎么起、功能清单、预埋 Bug 与修复、并发设计、提交约定，以及本节的人机协作过程。
- **git log** —— 落地视角：每个功能对应一次（或一组）提交，三者可互相印证"为什么这么改"。

> 一句话总结我们的配合：**你定方向、按功能下指令、逐步验收；我读代码、写实现、带测试、写文档——每一步都等你「继续」。**
