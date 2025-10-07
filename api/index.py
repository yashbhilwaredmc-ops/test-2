import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, Date, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/dmc_inventory.db")

engine = create_engine(DATABASE_URL, connect_args={} if not DATABASE_URL.startswith("sqlite") else {"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy models (schema mirrors the original Streamlit app)
class ITInventory(Base):
    __tablename__ = "it_inventory"
    id = Column(Integer, primary_key=True, index=True)
    assets_id = Column(String, unique=True, nullable=False)
    system_type = Column(String)
    location = Column(String)
    brand = Column(String)
    model = Column(String)
    serial_number = Column(String, unique=True)
    status = Column(String)
    windows = Column(String)
    config = Column(String)
    warranty_status = Column(String)
    last_audit_date = Column(String)
    remarks = Column(Text)


class InventoryTracker(Base):
    __tablename__ = "inventory_tracker"
    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String)
    assets_id = Column(String)
    system_type = Column(String)
    location = Column(String)
    brand = Column(String)
    model = Column(String)
    serial_number = Column(String)
    status = Column(String)
    windows = Column(String)
    config = Column(String)
    warranty_status = Column(String)
    date_of_allocation = Column(String)
    date_of_return = Column(String)
    last_audit_date = Column(String)
    phone_number = Column(String)
    extra_allocated_item = Column(Text)


# Pydantic schemas
class ITInventoryCreate(BaseModel):
    assets_id: str
    system_type: Optional[str] = None
    location: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    status: Optional[str] = None
    windows: Optional[str] = None
    config: Optional[str] = None
    warranty_status: Optional[str] = None
    last_audit_date: Optional[str] = None
    remarks: Optional[str] = None


class ITInventoryRead(ITInventoryCreate):
    id: int

    class Config:
        from_attributes = True


class TrackerCreate(BaseModel):
    employee_name: str
    assets_id: str
    system_type: Optional[str] = None
    location: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    status: Optional[str] = None
    windows: Optional[str] = None
    config: Optional[str] = None
    warranty_status: Optional[str] = None
    date_of_allocation: Optional[str] = None
    date_of_return: Optional[str] = None
    last_audit_date: Optional[str] = None
    phone_number: Optional[str] = None
    extra_allocated_item: Optional[str] = None


class TrackerRead(TrackerCreate):
    id: int

    class Config:
        from_attributes = True


app = FastAPI(title="DMC Inventory API", version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


# Health endpoint for Vercel checks
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# IT Inventory endpoints
@app.get("/api/it_inventory", response_model=List[ITInventoryRead])
def list_it_inventory(q: Optional[str] = None, status: Optional[str] = None) -> List[ITInventoryRead]:
    db = SessionLocal()
    try:
        query = db.query(ITInventory)
        if q:
            wildcard = f"%{q}%"
            query = query.filter(
                (ITInventory.assets_id.like(wildcard)) |
                (ITInventory.system_type.like(wildcard)) |
                (ITInventory.location.like(wildcard)) |
                (ITInventory.brand.like(wildcard)) |
                (ITInventory.model.like(wildcard)) |
                (ITInventory.serial_number.like(wildcard)) |
                (ITInventory.status.like(wildcard))
            )
        if status and status.lower() != "all":
            query = query.filter(ITInventory.status == status)
        return query.all()
    finally:
        db.close()


@app.post("/api/it_inventory", response_model=ITInventoryRead, status_code=201)
def create_it_inventory(payload: ITInventoryCreate) -> ITInventoryRead:
    if not payload.assets_id:
        raise HTTPException(status_code=400, detail="Assets ID is required")
    db = SessionLocal()
    try:
        # unique constraints might raise IntegrityError; let it bubble to 400
        item = ITInventory(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()


@app.delete("/api/it_inventory/{item_id}", status_code=204)
def delete_it_inventory(item_id: int) -> None:
    db = SessionLocal()
    try:
        item = db.query(ITInventory).filter(ITInventory.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(item)
        db.commit()
        return None
    finally:
        db.close()


# Inventory Tracker endpoints
@app.get("/api/inventory_tracker", response_model=List[TrackerRead])
def list_inventory_tracker(q: Optional[str] = None, status: Optional[str] = None) -> List[TrackerRead]:
    db = SessionLocal()
    try:
        query = db.query(InventoryTracker)
        if q:
            wildcard = f"%{q}%"
            query = query.filter(
                (InventoryTracker.employee_name.like(wildcard)) |
                (InventoryTracker.assets_id.like(wildcard)) |
                (InventoryTracker.system_type.like(wildcard)) |
                (InventoryTracker.location.like(wildcard)) |
                (InventoryTracker.brand.like(wildcard)) |
                (InventoryTracker.model.like(wildcard)) |
                (InventoryTracker.serial_number.like(wildcard)) |
                (InventoryTracker.status.like(wildcard))
            )
        if status and status.lower() != "all":
            query = query.filter(InventoryTracker.status == status)
        return query.all()
    finally:
        db.close()


@app.post("/api/inventory_tracker", response_model=TrackerRead, status_code=201)
def create_inventory_record(payload: TrackerCreate) -> TrackerRead:
    if not payload.employee_name or not payload.assets_id:
        raise HTTPException(status_code=400, detail="Employee Name and Assets ID are required")
    db = SessionLocal()
    try:
        rec = InventoryTracker(**payload.model_dump())
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
    finally:
        db.close()


@app.delete("/api/inventory_tracker/{record_id}", status_code=204)
def delete_inventory_record(record_id: int) -> None:
    db = SessionLocal()
    try:
        rec = db.query(InventoryTracker).filter(InventoryTracker.id == record_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
        db.delete(rec)
        db.commit()
        return None
    finally:
        db.close()


