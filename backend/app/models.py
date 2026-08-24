from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .db import Base


def utcnow():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow)


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=False)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    import_date = Column(String(10), nullable=False)
    channel = Column(String(120), index=True)
    status = Column(String(20), default="preview", index=True)
    summary_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))


class StagingRow(Base):
    __tablename__ = "staging_rows"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), nullable=False, index=True)
    sheet_name = Column(String(120), nullable=False)
    row_number = Column(Integer, nullable=False)
    kind = Column(String(20), default="data")
    date = Column(String(10), nullable=False)
    sku = Column(String(255), nullable=False, index=True)
    inventory = Column(Float)
    in_transit = Column(Float)
    yesterday_sales = Column(Float)
    seven_sales = Column(Float)
    thirty_sales = Column(Float)
    raw_json = Column(Text)
    product_fields_json = Column(Text)
    created_at = Column(DateTime, default=utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    sheet_name = Column(String(120), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    barcode = Column(String(255), index=True)
    product_code = Column(String(255), index=True)
    jd_code = Column(String(255))
    brand = Column(String(120), index=True)
    name = Column(String(500))
    spec = Column(String(255))
    color = Column(String(255))
    category = Column(String(255))
    supplier = Column(String(255))
    sale_price = Column(Float)
    purchase_price = Column(Float)
    grade = Column(String(120))
    status = Column(String(120))
    packaging = Column(String(255))
    material = Column(Text)
    notes = Column(Text)
    raw_json = Column(Text)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class SnapshotRow(Base):
    __tablename__ = "snapshot_rows"

    id = Column(Integer, primary_key=True)
    import_id = Column(Integer, ForeignKey("import_batches.id"), index=True)
    sheet_name = Column(String(120), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    date = Column(String(10), nullable=False, index=True)
    sku = Column(String(255), nullable=False, index=True)
    inventory = Column(Float)
    in_transit = Column(Float)
    yesterday_sales = Column(Float)
    seven_sales = Column(Float)
    thirty_sales = Column(Float)
    raw_json = Column(Text)
    created_at = Column(DateTime, default=utcnow)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, default="")
