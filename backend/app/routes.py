import csv
import io
import json
import re
import secrets
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import delete, func, insert, or_, select
from sqlalchemy.orm import Session

from .auth import (
    SESSION_COOKIE,
    create_session_token,
    get_current_user,
    hash_password,
    verify_password,
)
from .config import UPLOAD_DIR
from .db import get_db
from .models import ImportBatch, Product, Session as SessionModel, Setting, SnapshotRow, StagingRow, User
from .services.cleanup import cleanup_old_snapshots, get_retention_days
from .services.importer import (
    detect_date_from_filename,
    discard_staging,
    parse_workbook,
    store_staging,
)
from .sheet_schemas import DATA_SHEETS, PRODUCT_SHEETS, SHEET_BRAND

router = APIRouter(prefix="/api")


def json_body(value):
    return json.dumps(value, ensure_ascii=False)


def read_json(value, default=None):
    if not value:
        return default or {}
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default or {}


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def paginate(query, page, page_size):
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, rows


def latest_date(db: Session):
    return db.query(func.max(SnapshotRow.date)).scalar()


@router.post("/auth/login")
def login(payload: dict, request: Request, db: Session = Depends(get_db)):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_session_token(db, user.id)
    response = Response(
        content=json_body({"username": user.username}),
        media_type="application/json",
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=7 * 24 * 3600,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/auth/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.execute(delete(SessionModel).where(SessionModel.token == token))
        db.commit()
    response = Response(content=json_body({"ok": True}), media_type="application/json")
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"username": user.username}


@router.post("/auth/change-password")
def change_password(
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(str(payload.get("old_password", "")), user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    new_password = str(payload.get("new_password", ""))
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"ok": True}


@router.get("/meta/brands")
def brands(db: Session = Depends(get_db)):
    rows = db.query(Product.brand).distinct().all()
    brands = sorted({r[0] for r in rows if r[0]})
    return {"brands": brands}


@router.get("/meta/sheets")
def sheets():
    return {
        "data_sheets": DATA_SHEETS,
        "product_sheets": PRODUCT_SHEETS,
        "sheet_brand": SHEET_BRAND,
    }


@router.get("/dashboard/summary")
def dashboard_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    latest = latest_date(db)
    if not latest:
        return {
            "latest_date": None,
            "total_inventory": 0,
            "total_yesterday": 0,
            "total_seven": 0,
            "total_thirty": 0,
            "low_stock_count": 0,
            "low_stock": [],
            "channel_summary": [],
            "import_count": 0,
        }

    total_inventory = (
        db.query(func.sum(SnapshotRow.inventory))
        .filter(SnapshotRow.date == latest, SnapshotRow.sheet_name == "主仓")
        .scalar()
        or 0
    )
    total_yesterday = (
        db.query(func.sum(SnapshotRow.yesterday_sales))
        .filter(SnapshotRow.date == latest)
        .scalar()
        or 0
    )
    total_seven = (
        db.query(func.sum(SnapshotRow.seven_sales))
        .filter(SnapshotRow.date == latest)
        .scalar()
        or 0
    )
    total_thirty = (
        db.query(func.sum(SnapshotRow.thirty_sales))
        .filter(SnapshotRow.date == latest)
        .scalar()
        or 0
    )

    threshold_setting = db.get(Setting, "low_stock_threshold")
    threshold = int(threshold_setting.value or 10) if threshold_setting else 10
    low_stock_count = (
        db.query(func.count(func.distinct(SnapshotRow.sku)))
        .filter(
            SnapshotRow.date == latest,
            SnapshotRow.sheet_name.in_(DATA_SHEETS),
            SnapshotRow.inventory.isnot(None),
            SnapshotRow.inventory <= threshold,
        )
        .scalar()
        or 0
    )
    low_stock_rows = (
        db.query(SnapshotRow)
        .filter(
            SnapshotRow.date == latest,
            SnapshotRow.sheet_name.in_(DATA_SHEETS),
            SnapshotRow.inventory.isnot(None),
            SnapshotRow.inventory <= threshold,
        )
        .order_by(SnapshotRow.inventory.asc())
        .limit(50)
        .all()
    )
    low_stock = [
        {
            "sku": row.sku,
            "sheet_name": row.sheet_name,
            "brand": SHEET_BRAND.get(row.sheet_name, ""),
            "inventory": row.inventory,
            "name": product_name(db, row.sku),
        }
        for row in low_stock_rows
    ]

    channel_rows = (
        db.query(
            SnapshotRow.sheet_name,
            func.sum(SnapshotRow.inventory),
            func.sum(SnapshotRow.yesterday_sales),
            func.sum(SnapshotRow.seven_sales),
            func.sum(SnapshotRow.thirty_sales),
            func.count(SnapshotRow.id),
        )
        .filter(SnapshotRow.date == latest, SnapshotRow.sheet_name.in_(DATA_SHEETS))
        .group_by(SnapshotRow.sheet_name)
        .all()
    )
    channel_summary = [
        {
            "sheet_name": name,
            "brand": SHEET_BRAND.get(name, ""),
            "inventory": inv or 0,
            "yesterday_sales": y or 0,
            "seven_sales": seven or 0,
            "thirty_sales": thirty or 0,
            "sku_count": count,
        }
        for name, inv, y, seven, thirty, count in channel_rows
    ]
    import_count = db.query(func.count(ImportBatch.id)).filter(ImportBatch.status == "done").scalar() or 0
    return {
        "latest_date": latest,
        "total_inventory": round(total_inventory or 0, 2),
        "total_yesterday": round(total_yesterday or 0, 2),
        "total_seven": round(total_seven or 0, 2),
        "total_thirty": round(total_thirty or 0, 2),
        "low_stock_count": low_stock_count,
        "low_stock": low_stock,
        "channel_summary": channel_summary,
        "import_count": import_count,
    }


def product_name(db: Session, sku: str):
    product = (
        db.query(Product.name)
        .filter(or_(Product.barcode == sku, Product.product_code == sku))
        .first()
    )
    return product[0] if product and product[0] else ""


@router.get("/products")
def list_products(
    search: str = "",
    brand: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Product.barcode.like(like),
                Product.product_code.like(like),
                Product.name.like(like),
                Product.spec.like(like),
                Product.supplier.like(like),
            )
        )
    if brand:
        query = query.filter(Product.brand == brand)
    total, rows = paginate(query.order_by(Product.sheet_name, Product.row_number), page, page_size)
    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "sheet_name": p.sheet_name,
                "row_number": p.row_number,
                "barcode": p.barcode,
                "product_code": p.product_code,
                "jd_code": p.jd_code,
                "brand": p.brand,
                "name": p.name,
                "spec": p.spec,
                "color": p.color,
                "category": p.category,
                "supplier": p.supplier,
                "sale_price": p.sale_price,
                "purchase_price": p.purchase_price,
                "grade": p.grade,
                "status": p.status,
                "packaging": p.packaging,
                "material": p.material,
                "notes": p.notes,
                "raw_json": read_json(p.raw_json),
            }
            for p in rows
        ],
    }


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    for field in [
        "barcode",
        "product_code",
        "jd_code",
        "brand",
        "name",
        "spec",
        "color",
        "category",
        "supplier",
        "grade",
        "status",
        "packaging",
        "material",
        "notes",
    ]:
        if field in payload:
            setattr(product, field, str(payload[field]).strip() if payload[field] is not None else None)
    for field in ["sale_price", "purchase_price"]:
        if field in payload:
            setattr(product, field, to_float(payload[field]))
    db.commit()
    return {"ok": True}


@router.get("/inventory")
def list_inventory(
    brand: str = "",
    sheet: str = "",
    sku: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest = latest_date(db)
    if not latest:
        return {"total": 0, "items": [], "latest_date": None}
    query = db.query(SnapshotRow).filter(
        SnapshotRow.date == latest,
        SnapshotRow.sheet_name.in_(DATA_SHEETS),
        SnapshotRow.inventory.isnot(None),
    )
    if sheet:
        query = query.filter(SnapshotRow.sheet_name == sheet)
    elif brand:
        sheet_names = [name for name, b in SHEET_BRAND.items() if b == brand]
        query = query.filter(SnapshotRow.sheet_name.in_(sheet_names))
    if sku:
        query = query.filter(SnapshotRow.sku.like(f"%{sku}%"))
    total, rows = paginate(
        query.order_by(SnapshotRow.sheet_name, SnapshotRow.sku), page, page_size
    )
    return {
        "total": total,
        "latest_date": latest,
        "items": [
            {
                "id": row.id,
                "sku": row.sku,
                "sheet_name": row.sheet_name,
                "brand": SHEET_BRAND.get(row.sheet_name, ""),
                "inventory": row.inventory,
                "name": product_name(db, row.sku),
                "date": row.date,
            }
            for row in rows
        ],
    }


@router.get("/inventory/trend")
def inventory_trend(
    sku: str = Query(..., min_length=1),
    sheet: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SnapshotRow).filter(
        SnapshotRow.sku == sku,
        SnapshotRow.inventory.isnot(None),
    )
    if sheet:
        query = query.filter(SnapshotRow.sheet_name == sheet)
    rows = query.order_by(SnapshotRow.date.asc()).all()
    return {
        "sku": sku,
        "points": [
            {
                "date": row.date,
                "sheet_name": row.sheet_name,
                "inventory": row.inventory,
            }
            for row in rows
        ],
    }


@router.get("/sales")
def list_sales(
    brand: str = "",
    sheet: str = "",
    sku: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest = latest_date(db)
    if not latest:
        return {"total": 0, "items": [], "latest_date": None}
    query = db.query(SnapshotRow).filter(
        SnapshotRow.date == latest,
        SnapshotRow.sheet_name.in_(DATA_SHEETS),
        or_(
            SnapshotRow.yesterday_sales.isnot(None),
            SnapshotRow.seven_sales.isnot(None),
            SnapshotRow.thirty_sales.isnot(None),
        ),
    )
    if sheet:
        query = query.filter(SnapshotRow.sheet_name == sheet)
    elif brand:
        sheet_names = [name for name, b in SHEET_BRAND.items() if b == brand]
        query = query.filter(SnapshotRow.sheet_name.in_(sheet_names))
    if sku:
        query = query.filter(SnapshotRow.sku.like(f"%{sku}%"))
    total, rows = paginate(
        query.order_by(SnapshotRow.sheet_name, SnapshotRow.sku), page, page_size
    )
    return {
        "total": total,
        "latest_date": latest,
        "items": [
            {
                "id": row.id,
                "sku": row.sku,
                "sheet_name": row.sheet_name,
                "brand": SHEET_BRAND.get(row.sheet_name, ""),
                "yesterday_sales": row.yesterday_sales,
                "seven_sales": row.seven_sales,
                "thirty_sales": row.thirty_sales,
                "name": product_name(db, row.sku),
                "date": row.date,
            }
            for row in rows
        ],
    }


@router.get("/sales/trend")
def sales_trend(
    sku: str = Query(..., min_length=1),
    sheet: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SnapshotRow).filter(
        SnapshotRow.sku == sku,
        or_(
            SnapshotRow.yesterday_sales.isnot(None),
            SnapshotRow.seven_sales.isnot(None),
            SnapshotRow.thirty_sales.isnot(None),
        ),
    )
    if sheet:
        query = query.filter(SnapshotRow.sheet_name == sheet)
    rows = query.order_by(SnapshotRow.date.asc()).all()
    return {
        "sku": sku,
        "points": [
            {
                "date": row.date,
                "sheet_name": row.sheet_name,
                "yesterday_sales": row.yesterday_sales,
                "seven_sales": row.seven_sales,
                "thirty_sales": row.thirty_sales,
            }
            for row in rows
        ],
    }


@router.post("/imports/upload")
async def upload_import(
    file: UploadFile,
    include_master: bool = False,
    date: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    original_name = file.filename or "未命名.xlsx"
    if not original_name.lower().endswith((".xlsx", ".xlsm", ".xls")):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件")
    token = secrets.token_urlsafe(16)
    safe_name = re.sub(r"[^\w.\u4e00-\u9fff-]", "_", original_name)
    target = UPLOAD_DIR / f"{token}_{safe_name}"
    size = 0
    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)
            size += len(chunk)

    try:
        snapshot_date, sheet_summaries, rows = parse_workbook(
            target,
            snapshot_date=date if date else detect_date_from_filename(original_name),
            include_master=include_master,
        )
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"文件解析失败：{exc}") from exc

    if not rows:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="没有识别到可导入的数据 sheet")

    store_staging(db, token, rows)
    batch = ImportBatch(
        token=token,
        filename=original_name,
        file_size=size,
        import_date=snapshot_date,
        status="preview",
        summary_json=json_body(
            {
                "date": snapshot_date,
                "sheets": sheet_summaries,
                "total_rows": len(rows),
                "include_master": include_master,
            }
        ),
        created_by=user.id,
    )
    db.add(batch)
    db.commit()
    return {
        "token": token,
        "filename": original_name,
        "date": snapshot_date,
        "total_rows": len(rows),
        "sheets": sheet_summaries,
        "include_master": include_master,
    }


def confirm_import(db: Session, token: str):
    batch = db.query(ImportBatch).filter(ImportBatch.token == token).first()
    if not batch:
        raise HTTPException(status_code=404, detail="导入任务不存在")
    if batch.status != "preview":
        raise HTTPException(status_code=400, detail="导入任务已处理")

    staging = (
        db.query(StagingRow)
        .filter(StagingRow.token == token)
        .order_by(StagingRow.id)
        .all()
    )
    if not staging:
        raise HTTPException(status_code=400, detail="没有可确认的数据")

    db.add(batch)
    db.flush()
    import_id = batch.id

    previous_imports = (
        select(ImportBatch.id)
        .where(
            ImportBatch.import_date == batch.import_date,
            ImportBatch.status == "done",
        )
    )
    db.execute(delete(SnapshotRow).where(SnapshotRow.import_id.in_(previous_imports)))

    master_rows = [row for row in staging if row.kind == "master"]
    for row in master_rows:
        fields = read_json(row.product_fields_json)
        product = (
            db.query(Product)
            .filter(
                Product.sheet_name == row.sheet_name,
                Product.row_number == row.row_number,
            )
            .first()
        )
        values = {
            "sheet_name": row.sheet_name,
            "row_number": row.row_number,
            "barcode": fields.get("barcode"),
            "product_code": fields.get("product_code"),
            "jd_code": fields.get("jd_code"),
            "brand": fields.get("brand"),
            "name": fields.get("name"),
            "spec": fields.get("spec"),
            "color": fields.get("color"),
            "category": fields.get("category"),
            "supplier": fields.get("supplier"),
            "sale_price": fields.get("sale_price"),
            "purchase_price": fields.get("purchase_price"),
            "grade": fields.get("grade"),
            "status": fields.get("status"),
            "packaging": fields.get("packaging"),
            "material": fields.get("material"),
            "notes": fields.get("notes"),
            "raw_json": row.raw_json,
        }
        if product:
            for key, value in values.items():
                setattr(product, key, value)
        else:
            db.add(Product(**values))

    snapshot_values = []
    for row in staging:
        if row.kind == "master":
            continue
        snapshot_values.append(
            {
                "import_id": import_id,
                "sheet_name": row.sheet_name,
                "row_number": row.row_number,
                "date": row.date,
                "sku": row.sku,
                "inventory": row.inventory,
                "yesterday_sales": row.yesterday_sales,
                "seven_sales": row.seven_sales,
                "thirty_sales": row.thirty_sales,
                "raw_json": row.raw_json,
            }
        )
    for start in range(0, len(snapshot_values), 20_000):
        db.execute(insert(SnapshotRow), snapshot_values[start : start + 20_000])

    batch.status = "done"
    discard_staging(db, token)
    db.commit()
    cleanup_old_snapshots(db)
    return batch


@router.post("/imports/{token}/confirm")
def confirm_import_endpoint(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    batch = confirm_import(db, token)
    return {"ok": True, "import_id": batch.id, "filename": batch.filename}


@router.delete("/imports/{token}")
def discard_import(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    batch = db.query(ImportBatch).filter(ImportBatch.token == token).first()
    if batch:
        discard_staging(db, token)
        batch.status = "discarded"
        db.commit()
    return {"ok": True}


@router.get("/imports")
def list_imports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(ImportBatch)
        .order_by(ImportBatch.created_at.desc())
        .limit(100)
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "token": row.token,
                "filename": row.filename,
                "file_size": row.file_size,
                "import_date": row.import_date,
                "status": row.status,
                "summary": read_json(row.summary_json),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    threshold = db.get(Setting, "low_stock_threshold")
    return {
        "low_stock_threshold": int(threshold.value) if threshold and threshold.value else 10,
        "snapshot_retention_days": get_retention_days(db),
    }


@router.put("/settings")
def update_settings(
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_threshold = db.get(Setting, "low_stock_threshold")
    threshold = int(
        payload.get(
            "low_stock_threshold",
            current_threshold.value if current_threshold and current_threshold.value else 10,
        )
    )
    if threshold < 0:
        raise HTTPException(status_code=400, detail="预警值不能为负数")
    setting = db.get(Setting, "low_stock_threshold")
    if setting:
        setting.value = str(threshold)
    else:
        db.add(Setting(key="low_stock_threshold", value=str(threshold)))

    retention_days = int(payload.get("snapshot_retention_days", get_retention_days(db)))
    if not 1 <= retention_days <= 3650:
        raise HTTPException(status_code=400, detail="快照保留天数需要在 1 到 3650 之间")
    retention = db.get(Setting, "snapshot_retention_days")
    if retention:
        retention.value = str(retention_days)
    else:
        db.add(Setting(key="snapshot_retention_days", value=str(retention_days)))

    db.commit()
    return {
        "low_stock_threshold": threshold,
        "snapshot_retention_days": retention_days,
    }


@router.post("/settings/cleanup-snapshots")
def cleanup_snapshots(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted, cutoff = cleanup_old_snapshots(db)
    return {"deleted": deleted, "cutoff": cutoff}


@router.get("/export/{kind}")
def export_data(
    kind: str,
    brand: str = "",
    sheet: str = "",
    sku: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if kind not in ("products", "inventory", "sales"):
        raise HTTPException(status_code=400, detail="不支持的导出类型")

    if kind == "products":
        query = db.query(Product)
        if brand:
            query = query.filter(Product.brand == brand)
        if sku:
            query = query.filter(Product.barcode.like(f"%{sku}%"))
        rows = query.order_by(Product.sheet_name, Product.row_number).all()
        data = [
            {
                "品牌": p.brand,
                "来源表": p.sheet_name,
                "条形码": p.barcode,
                "产品编号": p.product_code,
                "京东/唯品条码": p.jd_code,
                "产品名称": p.name,
                "产品规格": p.spec,
                "颜色": p.color,
                "品类": p.category,
                "供应商": p.supplier,
                "等级": p.grade,
                "售卖价": p.sale_price,
                "采购价": p.purchase_price,
                "商品情况": p.status,
                "包装": p.packaging,
                "面料成分": p.material,
                "备注": p.notes,
            }
            for p in rows
        ]
    else:
        latest = latest_date(db)
        if not latest:
            data = []
        else:
            query = db.query(SnapshotRow).filter(SnapshotRow.date == latest)
            query = query.filter(SnapshotRow.sheet_name.in_(DATA_SHEETS))
            if sheet:
                query = query.filter(SnapshotRow.sheet_name == sheet)
            elif brand:
                sheet_names = [name for name, b in SHEET_BRAND.items() if b == brand]
                query = query.filter(SnapshotRow.sheet_name.in_(sheet_names))
            if sku:
                query = query.filter(SnapshotRow.sku.like(f"%{sku}%"))
            rows = query.order_by(SnapshotRow.sheet_name, SnapshotRow.sku).all()
            data = [
                {
                    "日期": row.date,
                    "来源表": row.sheet_name,
                    "品牌": SHEET_BRAND.get(row.sheet_name, ""),
                    "商品编码": row.sku,
                    "库存": row.inventory,
                    "昨日销量": row.yesterday_sales,
                    "7天销量": row.seven_sales,
                    "30天销量": row.thirty_sales,
                }
                for row in rows
            ]

    df = pd.DataFrame(data)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    filename = f"{kind}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
