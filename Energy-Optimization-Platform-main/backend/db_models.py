"""
SQLAlchemy Database Models for EnergiX Copilot
"""

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Machine(Base):
    __tablename__ = "machines"
    __table_args__ = {"schema": "energix"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    machine_id = Column(String(50), unique=True, nullable=False, index=True)
    machine_type = Column(String(50), nullable=False)
    plant_id = Column(String(20), nullable=False, index=True)
    zone_id = Column(String(20), nullable=False)
    rated_power_kw = Column(Numeric(10, 2), nullable=False)
    normal_load_min = Column(Integer, nullable=False)
    normal_load_max = Column(Integer, nullable=False)
    efficiency_baseline = Column(Numeric(5, 4), nullable=False)
    temp_sensitivity = Column(Numeric(5, 4), nullable=False)
    vibration_normal_min = Column(Numeric(5, 2), nullable=False)
    vibration_normal_max = Column(Numeric(5, 2), nullable=False)
    output_per_load = Column(Numeric(5, 2), nullable=False)
    shift_preference = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    last_maintenance_date = Column(DateTime)
    next_maintenance_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical', 'warning', 'info')", name="check_severity"
        ),
        CheckConstraint(
            "status IN ('active', 'acknowledged', 'resolved')", name="check_status"
        ),
        {"schema": "energix"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    machine_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    recommended_action = Column(String(100))
    status = Column(String(20), default="active")
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    anomaly_score = Column(Numeric(10, 6))
    actual_value = Column(Numeric(10, 2))
    expected_value = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint("priority IN ('high', 'medium', 'low')", name="check_priority"),
        CheckConstraint(
            "status IN ('pending', 'applied', 'dismissed')", name="check_rec_status"
        ),
        {"schema": "energix"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    machine_id = Column(String(50), nullable=True, index=True)
    plant_id = Column(String(20))
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    estimated_savings_kwh = Column(Numeric(10, 2))
    estimated_savings_percent = Column(Numeric(5, 2))
    estimated_roi_days = Column(Integer)
    difficulty = Column(String(20))
    status = Column(String(20), default="pending")
    applied_at = Column(DateTime)
    actual_savings_kwh = Column(Numeric(10, 2))
    generated_by = Column(String(50), default="sarvam_ai")
    confidence_score = Column(Numeric(5, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
