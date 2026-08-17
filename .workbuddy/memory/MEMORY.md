# 项目长期记忆

## Git 远程仓库
- 地址（SSH）：git@github.com:boltspectre/wms-test.git
- 默认分支：master
- 本地 master 已跟踪 origin/master，可直接 git pull / git push
- 拉取方式：SSH（HTTP 方式在沙箱中无法连接 github:443，改用 SSH 成功）
- 仓库内容：README / AI_USAGE_GUIDE（提交规范）/ TASKS / .gitignore / backend-java / backend-python / docs / frontend-react / frontend-vue

## 技术栈（已选定，依据 backend-python/AI分析文档.md）
- 后端：Python 3.12.9 + FastAPI + SQLAlchemy 2.0 + SQLite（aiosqlite）
- 前端：Vue 3 + Element Plus + Vite
- Java(SpringBoot) / React 两套未选用

## 运行环境（沙箱已落地）
- 后端 venv：`backend-python/.venv`（系统 Python 3.12.9 建；managed 3.13/3.14 的 venv 缺 pip 不可用；旧 `.venv` 改名 `.venv_broken` 保留，未删）
- 包索引：必须用官方 PyPI `https://pypi.org/simple`（沙箱清华镜像对 uv/fastapi 返回空）
- 装依赖：`pip install uv` → `uv sync --frozen`（uv.lock）
- 种子数据：`cd backend-python && .venv/Scripts/python.exe init_data.py` → 生成 wms.db
- 启动后端：`cd backend-python && .venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`（沙箱 --reload 不生效，改代码后须 `taskkill /F /IM python.exe` 杀全部 python 再重启，否则残留 uvicorn 竞争 8000 致诡异 500）
- 启动前端：`cd frontend-vue && npm run dev`（:5173，/api 代理 8000）
- 红线：环境+启动完成后不改业务代码，等用户“开始修复”指令

## 工作约定（WMS 任务执行流程）
- 推进单位 = **完整功能**：同一功能的前后端一起改（除非该功能纯后端、无前端）；前端若本来无问题则不改动。改完按功能汇报，并**必须附带【网页操作步骤 + 正确预期结果】**（不仅是 curl/API 测试），等用户确认「继续」再做下一个功能。
- 关键发现：后端 schemas/router 用 snake_case，但前端 api/index.ts 与 API_SPEC.md 用 camelCase；新接口一律用 Pydantic alias 让后端兼容 camelCase，不改前端。
- AI分析文档.md 称 inventory.py 入库/库存接口「已实现」不实，实际是 stub（raise 501）；必做1/2 后端都需自己实现。

## 项目任务（TASKS.md / plan.md，逐项推进）
- 必做1：入库单（后端 inventory.py ✅已做①；前端 InboundView.vue ✅已做②）
- 必做2：库存查询（后端 inventory.py ✅已做③；前端 InventoryView.vue ✅已做④）
- 必做3：Bug 修复（后端 products.py 删除校验 待⑤；前端 ProductsView.vue 跳页 待⑥）
- 选做 A 出库单+并发；B 单元测试；C 前端性能
- 提交前需写根目录 NOTES.md（AI 使用说明 + Bug 记录）
