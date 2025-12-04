"""API routes for schema management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    SchemaResponse, SchemaWithVersions,
    SchemaVersionResponse, SchemaVersionDetail,
    SchemaDiffRequest, SchemaDiffResponse
)
from app.services.schema_service import SchemaService

router = APIRouter(prefix="/schemas", tags=["schemas"])


@router.post("/", response_model=SchemaVersionResponse, status_code=201)
async def upload_schema(
    name: str = Form(..., description="Schema name"),
    file: UploadFile = File(..., description="Schema YAML file"),
    version: Optional[str] = Form(None, description="Version identifier (auto-generated if not provided)"),
    description: Optional[str] = Form(None, description="Schema description (only used for new schemas)"),
    notes: Optional[str] = Form(None, description="Version notes"),
    created_by: Optional[str] = Form(None, description="Creator identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a schema. If the schema name exists, creates a new version.
    If the schema name is new, creates the schema and its first version.

    Version numbers are auto-generated (incrementing from 1.0.0) if not provided.
    """
    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8')

    # Check if schema exists
    existing = await SchemaService.get_schema_by_name(db, name)

    if existing:
        # Schema exists - create new version
        # Auto-generate version if not provided
        if not version:
            versions = await SchemaService.list_schema_versions(db, existing.id)
            version = SchemaService.generate_next_version(versions)

        schema_version, error = await SchemaService.create_schema_version(
            db, existing.id, version, content_str, created_by, notes
        )

        if error:
            raise HTTPException(status_code=400, detail=error)

        return schema_version
    else:
        # Schema doesn't exist - create schema + first version
        new_schema = await SchemaService.create_schema(db, name, description)

        # Use provided version or default to 1.0.0
        if not version:
            version = "1.0.0"

        schema_version, error = await SchemaService.create_schema_version(
            db, new_schema.id, version, content_str, created_by, notes
        )

        if error:
            # Clean up schema if version creation fails
            await SchemaService.delete_schema(db, new_schema.id)
            raise HTTPException(status_code=400, detail=error)

        return schema_version


@router.get("/", response_model=List[SchemaResponse])
async def list_schemas(db: AsyncSession = Depends(get_db)):
    """List all schemas."""
    schemas = await SchemaService.list_schemas(db)
    return schemas


@router.get("/{schema_name}", response_model=SchemaWithVersions)
async def get_schema(
    schema_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a schema by name with all its versions."""
    schema = await SchemaService.get_schema_by_name(db, schema_name)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema


@router.delete("/{schema_name}", status_code=204)
async def delete_schema(
    schema_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a schema and all its versions."""
    schema = await SchemaService.get_schema_by_name(db, schema_name)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    await SchemaService.delete_schema(db, schema.id)
    return None


@router.post("/{schema_name}/versions", response_model=SchemaVersionResponse, status_code=201)
async def create_schema_version(
    schema_name: str,
    version: str = Form(...),
    notes: str = Form(None),
    created_by: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new version of a schema."""
    # Get schema
    schema = await SchemaService.get_schema_by_name(db, schema_name)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8')

    # Create version
    schema_version, error = await SchemaService.create_schema_version(
        db, schema.id, version, content_str, created_by, notes
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return schema_version


@router.get("/{schema_name}/versions", response_model=List[SchemaVersionResponse])
async def list_schema_versions(
    schema_name: str,
    db: AsyncSession = Depends(get_db)
):
    """List all versions of a schema."""
    schema = await SchemaService.get_schema_by_name(db, schema_name)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    versions = await SchemaService.list_schema_versions(db, schema.id)
    return versions


@router.get("/{schema_name}/versions/{version}", response_model=SchemaVersionDetail)
async def get_schema_version(
    schema_name: str,
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific version of a schema."""
    schema_version = await SchemaService.get_schema_version(db, schema_name, version)
    if not schema_version:
        raise HTTPException(status_code=404, detail="Schema version not found")
    return schema_version


@router.post("/{schema_name}/diff", response_model=SchemaDiffResponse)
async def get_schema_diff(
    schema_name: str,
    diff_request: SchemaDiffRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get the diff between two schema versions."""
    # Verify schema name matches
    if diff_request.schema_name != schema_name:
        raise HTTPException(status_code=400, detail="Schema name mismatch")

    # Get both versions
    version1 = await SchemaService.get_schema_version(db, schema_name, diff_request.version1)
    version2 = await SchemaService.get_schema_version(db, schema_name, diff_request.version2)

    if not version1:
        raise HTTPException(status_code=404, detail=f"Version {diff_request.version1} not found")
    if not version2:
        raise HTTPException(status_code=404, detail=f"Version {diff_request.version2} not found")

    # Generate diff
    diff, changes_summary = SchemaService.get_schema_diff(version1.content, version2.content)

    return SchemaDiffResponse(
        schema_name=schema_name,
        version1=diff_request.version1,
        version2=diff_request.version2,
        diff=diff,
        changes_summary=changes_summary
    )
