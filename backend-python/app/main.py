from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import engine, Base
from app.routers import products, warehouses, inventory

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WMS API",
    description="仓储管理系统 API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 全局异常处理器：统一为 API_SPEC 的 {code, message, data:null} 包络 ============

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # 成功响应由各路由自己返回 {code,message,data}；此处仅统一「错误」响应格式
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": str(exc.detail), "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic 校验失败（如 quantity<=0、字段缺失），按规范返回 422 + 统一包络
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "请求参数校验失败", "data": None},
    )


# 注册路由
app.include_router(products.router)
app.include_router(warehouses.router)
app.include_router(inventory.router)


@app.get("/")
def root():
    return {"message": "WMS API is running. Visit /docs for API documentation."}
