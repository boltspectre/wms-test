"""
WMS 后端单元测试（选做 B）

使用 FastAPI TestClient + 独立的临时 SQLite 数据库，
完全不依赖、也不污染项目真实的 wms.db。

运行方式（在 backend-python 目录下，venv 已装 pytest + httpx）：
    .venv/Scripts/python.exe -m pytest test_wms.py -v

覆盖：
- 入库单创建（库存累加、单号、非法商品/库位 400、空明细 422）
- 库存查询（keyword / warehouseId 过滤、分页）
- 出库单创建（库存原子扣减、库存不足 400、无库存 400、空明细 422）
- 商品删除（存在关联库存→400，无关联库存→200）
"""
import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Product, Warehouse, Location, Inventory


@pytest.fixture
def client_db():
    """搭建一个临时数据库 + 种子数据，并覆盖 get_db 依赖。"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False}
    )
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # ---- 种子数据（与 init_data.py 保持一致）----
    db = SessionFactory()
    p1 = Product(name="蓝牙耳机 Pro", sku="SKU-001", unit="个")
    p2 = Product(name="Type-C 数据线", sku="SKU-002", unit="条")
    p3 = Product(name="无线充电板", sku="SKU-003", unit="个")
    p4 = Product(name="手机壳 透明款", sku="SKU-004", unit="个")
    p5 = Product(name="屏幕保护膜", sku="SKU-005", unit="张")
    db.add_all([p1, p2, p3, p4, p5])
    db.flush()

    wh1 = Warehouse(code="WH-A", name="广州主仓")
    wh2 = Warehouse(code="WH-B", name="深圳保税仓")
    db.add_all([wh1, wh2])
    db.flush()

    loc1 = Location(warehouse_id=wh1.id, code="WH-A-01-01", status="OCCUPIED")
    loc2 = Location(warehouse_id=wh1.id, code="WH-A-01-02", status="OCCUPIED")
    loc3 = Location(warehouse_id=wh1.id, code="WH-A-02-01", status="FREE")
    loc4 = Location(warehouse_id=wh2.id, code="WH-B-01-01", status="FREE")
    db.add_all([loc1, loc2, loc3, loc4])
    db.flush()

    db.add_all([
        Inventory(product_id=p1.id, location_code=loc1.code, quantity=150),
        Inventory(product_id=p1.id, location_code=loc2.code, quantity=80),
        Inventory(product_id=p2.id, location_code=loc1.code, quantity=300),
        Inventory(product_id=p3.id, location_code=loc2.code, quantity=5),
        Inventory(product_id=p4.id, location_code=loc1.code, quantity=8),
    ])
    db.commit()
    db.close()

    # ---- 覆盖 FastAPI 的数据库依赖 ----
    def override_get_db():
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client, SessionFactory

    app.dependency_overrides.clear()
    engine.dispose()
    os.remove(path)


def _qty(SessionFactory, product_id, location_code):
    s = SessionFactory()
    inv = s.query(Inventory).filter_by(
        product_id=product_id, location_code=location_code
    ).first()
    s.close()
    return inv.quantity if inv else None


# ===================== 入库单 =====================

def test_create_inbound_order_success(client_db):
    c, S = client_db
    r = c.post(
        "/api/inbound-orders",
        json={
            "supplierName": "测试供应商",
            "items": [{"productId": 1, "quantity": 50, "locationCode": "WH-A-01-01"}],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["code"] == 201
    assert body["data"]["orderNo"].startswith("IN-")
    assert body["data"]["items"][0]["quantity"] == 50
    # 库存 150 -> 200
    assert _qty(S, 1, "WH-A-01-01") == 200


def test_create_inbound_order_missing_product(client_db):
    c, S = client_db
    r = c.post(
        "/api/inbound-orders",
        json={
            "supplierName": "X",
            "items": [{"productId": 999, "quantity": 1, "locationCode": "WH-A-01-01"}],
        },
    )
    assert r.status_code == 400


def test_create_inbound_order_missing_location(client_db):
    c, S = client_db
    r = c.post(
        "/api/inbound-orders",
        json={
            "supplierName": "X",
            "items": [{"productId": 1, "quantity": 1, "locationCode": "NO-SUCH-LOC"}],
        },
    )
    assert r.status_code == 400


def test_create_inbound_order_empty_items_422(client_db):
    c, S = client_db
    r = c.post("/api/inbound-orders", json={"supplierName": "X", "items": []})
    assert r.status_code == 422


# ===================== 库存查询 =====================

def test_query_inventory_keyword(client_db):
    c, S = client_db
    r = c.get("/api/inventory", params={"keyword": "耳机"})
    body = r.json()
    assert body["code"] == 200
    # 蓝牙耳机 Pro 在 WH-A-01-01 与 WH-A-01-02 各一条 -> 2 条
    assert body["data"]["total"] == 2
    assert all("耳机" in it["productName"] for it in body["data"]["list"])


def test_query_inventory_by_warehouse(client_db):
    c, S = client_db
    r = c.get("/api/inventory", params={"warehouseId": 2})  # 深圳保税仓 WH-B
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 0  # 种子数据全部在广州主仓


# ===================== 出库单 =====================

def test_create_outbound_order_success(client_db):
    c, S = client_db
    r = c.post(
        "/api/outbound-orders",
        json={
            "customerName": "测试客户",
            "items": [{"productId": 1, "quantity": 10, "locationCode": "WH-A-01-01"}],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["code"] == 201
    assert body["data"]["orderNo"].startswith("OUT-")
    # 库存 150 -> 140
    assert _qty(S, 1, "WH-A-01-01") == 140


def test_create_outbound_order_insufficient_stock(client_db):
    c, S = client_db
    # 无线充电板 WH-A-01-02 仅有 5，出库 10
    r = c.post(
        "/api/outbound-orders",
        json={
            "customerName": "X",
            "items": [{"productId": 3, "quantity": 10, "locationCode": "WH-A-01-02"}],
        },
    )
    assert r.status_code == 400
    # 库存不应改变
    assert _qty(S, 3, "WH-A-01-02") == 5


def test_create_outbound_order_no_inventory(client_db):
    c, S = client_db
    # 屏幕保护膜(p5) 没有任何库存
    r = c.post(
        "/api/outbound-orders",
        json={
            "customerName": "X",
            "items": [{"productId": 5, "quantity": 1, "locationCode": "WH-A-01-01"}],
        },
    )
    assert r.status_code == 400


def test_create_outbound_order_empty_items_422(client_db):
    c, S = client_db
    r = c.post("/api/outbound-orders", json={"customerName": "X", "items": []})
    assert r.status_code == 422


def test_list_outbound_orders(client_db):
    c, S = client_db
    c.post(
        "/api/outbound-orders",
        json={
            "customerName": "测试客户",
            "items": [{"productId": 2, "quantity": 5, "locationCode": "WH-A-01-01"}],
        },
    )
    r = c.get("/api/outbound-orders", params={"page": 1, "pageSize": 20})
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["total"] >= 1


# ===================== 商品删除 Bug 修复 =====================

def test_delete_product_with_inventory_400(client_db):
    c, S = client_db
    # 商品 1 存在关联库存 -> 400
    r = c.delete("/api/products/1")
    assert r.status_code == 400


def test_delete_product_without_inventory_200(client_db):
    c, S = client_db
    # 商品 5 没有关联库存 -> 200
    r = c.delete("/api/products/5")
    assert r.status_code == 200
