from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, ForeignKey,
    JSON, Index, UniqueConstraint, text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.infra.db.database import Base

# ===== Lookups =====
class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

class ActivityType(Base):
    __tablename__ = "activity_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

class AnomalyType(Base):
    __tablename__ = "anomaly_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    severity_default: Mapped[int] = mapped_column(Integer, server_default=text("1"))

# ===== Core =====
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(128))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    risk_score: Mapped[float] = mapped_column(Float, server_default=text("0"))
    anomaly_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    role = relationship("Role")
    logs = relationship("Log", back_populates="user")
    anomalies = relationship("Anomaly", back_populates="user")

class Log(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activity_type_id: Mapped[int] = mapped_column(ForeignKey("activity_types.id"))
    source_ip: Mapped[str | None] = mapped_column(String(64))
    params_json: Mapped[dict | None] = mapped_column(JSON)
    hour: Mapped[int | None] = mapped_column(Integer)
    is_weekend: Mapped[bool | None] = mapped_column(Boolean)
    is_night: Mapped[bool | None] = mapped_column(Boolean)

    user = relationship("User")
    activity_type = relationship("ActivityType")

    __table_args__ = (
        Index("ix_logs_user_ts", "user_id", "ts"),
        Index("ix_logs_activity_ts", "activity_type_id", "ts"),
    )

class Anomaly(Base):
    __tablename__ = "anomalies"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    anomaly_type_id: Mapped[int] = mapped_column(ForeignKey("anomaly_types.id"))
    score: Mapped[float] = mapped_column(Float)
    risk: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), server_default=text("'open'"))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    evidence_json: Mapped[dict | None] = mapped_column(JSON)

    user = relationship("User", back_populates="anomalies")
    anomaly_type = relationship("AnomalyType")

    __table_args__ = (
        Index("ix_anom_user_status", "user_id", "status"),
        Index("ix_anom_type_ts", "anomaly_type_id", "detected_at"),
    )
