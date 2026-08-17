"""
============================================
 候选人需要实现以下接口：
============================================

POST /api/inbound-orders   — 创建入库单（任务1）
GET  /api/inventory         — 库存查询（任务2）

提示：
- 参考 routers/products.py 的实现风格
- 使用 SQLAlchemy 进行数据库操作
- 入库单创建需要使用事务（db.commit / db.rollback）
- 库存查询需要 JOIN 多表获取商品名、仓库名
- 注意 SQL 注入防护（使用参数化查询）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from datetime import date

from app.database import get_db
from app.models import Product, Location, Inventory, Warehouse, InboundOrder, InboundOrderItem
from app.schemas import InboundOrderCreate

router = APIRouter(tags=["库存 & 入库"])


def _gen_order_no(db: Session) -> str:
    """生成入库单号 IN-YYYYMMDD-XXX，XXX = 当日已存在单数 + 1（三位补零）"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"IN-{today}-"
    count = db.query(InboundOrder).filter(InboundOrder.order_no.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"


@router.post("/api/inbound-orders", status_code=201)
def create_inbound_order(req: InboundOrderCreate, db: Session = Depends(get_db)):
    """
    创建入库单

    要求：
    1. 生成入库单号 IN-YYYYMMDD-XXX
    2. 校验商品和库位是否存在、数量合法
    3. 在事务中同时创建入库单 + 累加库存（一致性保证）
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="入库明细不能为空")

    # 单号唯一冲突最多重试 5 次
    for _ in range(5):
        order_no = _gen_order_no(db)
        order = InboundOrder(
            order_no=order_no,
            supplier_name=req.supplier_name,
            status="COMPLETED",
        )
        db.add(order)
        try:
            db.flush()  # 先落入库单，触发 order_no 唯一约束检测
        except IntegrityError:
            db.rollback()
            continue  # 单号冲突，重新生成

        try:
            item_responses = []
            for item in req.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    raise HTTPException(status_code=400, detail=f"商品不存在: id={item.product_id}")
                location = db.query(Location).filter(Location.code == item.location_code).first()
                if not location:
                    raise HTTPException(status_code=400, detail=f"库位不存在: {item.location_code}")

                db.add(InboundOrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    location_code=item.location_code,
                ))

                # 累加库存：同一 (product_id, location_code) 已存在则更新，否则新建
                inv = db.query(Inventory).filter(
                    Inventory.product_id == item.product_id,
                    Inventory.location_code == item.location_code,
                ).first()
                if inv:
                    inv.quantity += item.quantity
                else:
                    inv = Inventory(
                        product_id=item.product_id,
                        location_code=item.location_code,
                        quantity=item.quantity,
                    )
                    db.add(inv)

                item_responses.append({
                    "productId": item.product_id,
                    "productName": product.name,
                    "quantity": item.quantity,
                    "locationCode": item.location_code,
                })

            db.commit()
            db.refresh(order)
            return {
                "code": 201,
                "message": "入库单创建成功",
                "data": {
                    "id": order.id,
                    "orderNo": order.order_no,
                    "supplierName": order.supplier_name,
                    "status": order.status,
                    "items": item_responses,
                    "createdAt": order.created_at.isoformat() if order.created_at else None,
                },
            }
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="数据冲突，请重试")

    raise HTTPException(status_code=500, detail="生成入库单号失败，请重试")


@router.get("/api/inventory")
def query_inventory(
    keyword: str | None = Query(default=None, description="商品名称/SKU 模糊搜索"),
    warehouse_id: int | None = Query(default=None, alias="warehouseId", description="仓库ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
):
    """
    库存查询

    要求：
    1. 支持按 keyword 模糊搜索（商品名称/SKU）
    2. 支持按 warehouseId 筛选
    3. 支持分页
    4. 返回关联的商品名称、SKU、仓库名称

    注意：前端 api/index.ts 使用 camelCase 参数（warehouseId / pageSize），
    这里通过 Query(alias=...) 兼容，无需修改前端。
    """
    # 基础查询：inventory JOIN product / location / warehouse（均为 1:1）
    base = (
        db.query(Inventory, Product, Location, Warehouse)
        .join(Product, Inventory.product_id == Product.id)
        .join(Location, Inventory.location_code == Location.code)
        .join(Warehouse, Location.warehouse_id == Warehouse.id)
    )

    # 关键字过滤（商品名称 / SKU 模糊匹配，参数化防止注入）
    if keyword:
        kw = f"%{keyword}%"
        base = base.filter(or_(Product.name.like(kw), Product.sku.like(kw)))

    # 仓库过滤
    if warehouse_id is not None:
        base = base.filter(Location.warehouse_id == warehouse_id)

    # 总数（1:1 JOIN，行数即库存记录数）
    total = base.count()

    # 分页
    offset = (page - 1) * page_size
    rows = (
        base.order_by(Inventory.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for inv, prod, loc, wh in rows:
        items.append({
            "productId": prod.id,
            "productName": prod.name,
            "sku": prod.sku,
            "locationCode": loc.code,
            "warehouseName": wh.name,
            "quantity": inv.quantity,
            "updatedAt": inv.updated_at.isoformat() if inv.updated_at else None,
        })

    return {
        "code": 200,
        "data": {
            "list": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }
