from __future__ import annotations
from sqlalchemy import String, Text, Integer, Float, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    target_path: Mapped[str] = mapped_column(Text)
    ruleset: Mapped[str] = mapped_column(Text)
    ai_review: Mapped[bool] = mapped_column(default=True)
    policy_path: Mapped[str] = mapped_column(Text, default="policies/default.yml")

    decision: Mapped[str] = mapped_column(String(32), default="manual_review")
    decision_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    findings = relationship("Finding", back_populates="job", cascade="all, delete-orphan")
    model_calls = relationship("ModelCall", back_populates="job", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="job", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    file: Mapped[str] = mapped_column(Text)
    line: Mapped[int] = mapped_column(Integer)
    match: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text, default="")
    remediation: Mapped[str] = mapped_column(Text, default="")

    job = relationship("Job", back_populates="findings")

class ModelCall(Base):
    __tablename__ = "model_calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(32))  # analyzer|judge
    request_hash: Mapped[str] = mapped_column(String(64))
    response_excerpt: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="model_calls")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128), default="system")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="audit_events")


class Webhook(Base):
    __tablename__ = "webhooks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text)
    events: Mapped[dict] = mapped_column(JSON, default=list)  # ["scan.completed", "policy.block"]
    secret: Mapped[str] = mapped_column(String(128), default="")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FindingSuppression(Base):
    __tablename__ = "finding_suppressions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    rule_id: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    suppressed_by: Mapped[str] = mapped_column(String(128), default="")
    expires_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
