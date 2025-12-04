"""API routes for data validation."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import get_db
from app.schemas import ValidationResponse, ValidationResult
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("/", response_model=ValidationResponse)
async def validate_file(
    schema_name: str = Form(...),
    schema_version: str = Form(...),
    file: UploadFile = File(...),
    validation_config: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a data file against a schema.

    Upload a CSV, TSV, YAML, or JSON file to validate against the specified schema version.
    Optionally provide validation configuration as a JSON string.
    """
    # Parse validation config if provided
    config = None
    if validation_config:
        try:
            config = json.loads(validation_config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid validation config JSON")

    # Read file content
    content = await file.read()

    # Validate
    validation_result, is_valid, status = await ValidationService.validate_file(
        db,
        schema_name,
        schema_version,
        content,
        file.filename,
        config
    )

    # Get the validation log ID (last inserted)
    logs = await ValidationService.get_validation_logs(db, schema_name, limit=1)
    validation_id = logs[0].id if logs else 0

    return ValidationResponse(
        validation_id=validation_id,
        schema_name=schema_name,
        schema_version=schema_version,
        filename=file.filename,
        result=ValidationResult(
            is_valid=is_valid,
            errors=validation_result['errors'],
            warnings=validation_result['warnings'],
            summary=validation_result['summary']
        ),
        created_at=logs[0].created_at if logs else None
    )


@router.get("/logs", response_model=List[dict])
async def get_validation_logs(
    schema_name: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get validation logs, optionally filtered by schema name."""
    logs = await ValidationService.get_validation_logs(db, schema_name, limit)

    return [
        {
            'id': log.id,
            'schema_name': log.schema_name,
            'schema_version': log.schema_version,
            'filename': log.filename,
            'is_valid': log.is_valid,
            'created_at': log.created_at,
            'validation_result': json.loads(log.validation_result)
        }
        for log in logs
    ]


@router.get("/logs/{validation_id}")
async def get_validation_log(
    validation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific validation log by ID."""
    from sqlalchemy import select
    from app.models import ValidationLog

    result = await db.execute(
        select(ValidationLog).where(ValidationLog.id == validation_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Validation log not found")

    return {
        'id': log.id,
        'schema_name': log.schema_name,
        'schema_version': log.schema_version,
        'filename': log.filename,
        'is_valid': log.is_valid,
        'created_at': log.created_at,
        'validation_result': json.loads(log.validation_result)
    }
