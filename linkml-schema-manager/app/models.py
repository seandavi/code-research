"""Database models for schema storage."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Schema(Base):
    """Model for storing schema metadata."""
    __tablename__ = "schemas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    versions = relationship("SchemaVersion", back_populates="schema", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Schema(id={self.id}, name='{self.name}')>"


class SchemaVersion(Base):
    """Model for storing schema versions."""
    __tablename__ = "schema_versions"

    id = Column(Integer, primary_key=True, index=True)
    schema_id = Column(Integer, ForeignKey("schemas.id"), nullable=False)
    version = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)  # YAML content
    file_path = Column(String(500), nullable=False)  # Path to stored file
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)  # Optional: user who created this version
    notes = Column(Text, nullable=True)  # Optional: version notes

    # Relationships
    schema = relationship("Schema", back_populates="versions")

    # Composite index for schema_id and version
    __table_args__ = (
        Index('idx_schema_version', 'schema_id', 'version', unique=True),
    )

    def __repr__(self):
        return f"<SchemaVersion(id={self.id}, schema_id={self.schema_id}, version='{self.version}')>"


class ValidationLog(Base):
    """Model for storing validation requests and results."""
    __tablename__ = "validation_logs"

    id = Column(Integer, primary_key=True, index=True)
    schema_name = Column(String(255), nullable=False, index=True)
    schema_version = Column(String(50), nullable=False)
    filename = Column(String(500), nullable=False)
    validation_result = Column(Text, nullable=False)  # JSON-serialized validation results
    is_valid = Column(String(10), nullable=False)  # 'valid', 'invalid', 'error'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ValidationLog(id={self.id}, schema_name='{self.schema_name}', is_valid='{self.is_valid}')>"
