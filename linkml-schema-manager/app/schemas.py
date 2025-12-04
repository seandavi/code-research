"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Schema models
class SchemaBase(BaseModel):
    """Base schema for Schema."""
    name: str = Field(..., description="Unique name for the schema")
    description: Optional[str] = Field(None, description="Description of the schema")


class SchemaCreate(SchemaBase):
    """Schema for creating a new schema."""
    pass


class SchemaResponse(SchemaBase):
    """Schema for schema response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema Version models
class SchemaVersionBase(BaseModel):
    """Base schema for SchemaVersion."""
    version: str = Field(..., description="Version identifier (e.g., 1.0.0)")
    notes: Optional[str] = Field(None, description="Notes about this version")


class SchemaVersionCreate(SchemaVersionBase):
    """Schema for creating a new schema version."""
    pass


class SchemaVersionResponse(SchemaVersionBase):
    """Schema for schema version response."""
    id: int
    schema_id: int
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class SchemaVersionDetail(SchemaVersionResponse):
    """Detailed schema version response including content."""
    content: str = Field(..., description="YAML content of the schema")


# Schema with versions
class SchemaWithVersions(SchemaResponse):
    """Schema response including all versions."""
    versions: List[SchemaVersionResponse] = []


# Validation models
class ValidationRequest(BaseModel):
    """Request for validating data against a schema."""
    schema_name: str = Field(..., description="Name of the schema to validate against")
    schema_version: str = Field(..., description="Version of the schema")
    validation_config: Optional[Dict[str, Any]] = Field(None, description="Optional validation configuration")


class ValidationResult(BaseModel):
    """Result of a validation operation."""
    is_valid: bool = Field(..., description="Whether the validation passed")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of validation errors")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="List of validation warnings")
    summary: str = Field(..., description="Summary of validation results")


class ValidationResponse(BaseModel):
    """Response for validation request."""
    validation_id: int
    schema_name: str
    schema_version: str
    filename: str
    result: ValidationResult
    created_at: datetime


# Code generation models
class CodeGenerationRequest(BaseModel):
    """Request for code generation."""
    schema_name: str
    schema_version: str
    language: str = Field(..., description="Target language (python, typescript, etc.)")
    options: Optional[Dict[str, Any]] = Field(None, description="Language-specific options")


class CodeGenerationResponse(BaseModel):
    """Response for code generation."""
    schema_name: str
    schema_version: str
    language: str
    code: str = Field(..., description="Generated code")
    files: Optional[Dict[str, str]] = Field(None, description="Multiple files if applicable")


# Diff models
class SchemaDiffRequest(BaseModel):
    """Request for schema diff."""
    schema_name: str
    version1: str
    version2: str


class SchemaDiffResponse(BaseModel):
    """Response for schema diff."""
    schema_name: str
    version1: str
    version2: str
    diff: str = Field(..., description="Unified diff between versions")
    changes_summary: Dict[str, Any] = Field(..., description="Summary of changes")
