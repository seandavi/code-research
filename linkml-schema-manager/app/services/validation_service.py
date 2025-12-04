"""Service for data validation operations."""
import json
import csv
import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ValidationLog, SchemaVersion
from app.services.schema_service import SchemaService


class ValidationService:
    """Service for validating data files against LinkML schemas."""

    @staticmethod
    async def validate_file(
        db: AsyncSession,
        schema_name: str,
        schema_version: str,
        file_content: bytes,
        filename: str,
        validation_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], bool, str]:
        """
        Validate a data file against a schema.

        Returns:
            Tuple of (validation_result, is_valid, status_string)
        """
        # Get schema version
        schema_ver = await SchemaService.get_schema_version(
            db, schema_name, schema_version
        )

        if not schema_ver:
            return {
                'errors': [{'message': f'Schema {schema_name} version {schema_version} not found'}],
                'warnings': [],
                'summary': 'Schema not found'
            }, False, 'error'

        # Parse file content based on extension
        try:
            file_ext = Path(filename).suffix.lower()

            if file_ext in ['.csv', '.tsv']:
                data = ValidationService._parse_csv(
                    file_content.decode('utf-8'),
                    delimiter='\t' if file_ext == '.tsv' else ','
                )
            elif file_ext in ['.yaml', '.yml']:
                data = yaml.safe_load(file_content.decode('utf-8'))
            elif file_ext == '.json':
                data = json.loads(file_content.decode('utf-8'))
            else:
                return {
                    'errors': [{'message': f'Unsupported file type: {file_ext}'}],
                    'warnings': [],
                    'summary': 'Unsupported file type'
                }, False, 'error'
        except Exception as e:
            return {
                'errors': [{'message': f'Failed to parse file: {str(e)}'}],
                'warnings': [],
                'summary': 'File parsing error'
            }, False, 'error'

        # Perform validation
        try:
            validation_result = ValidationService._validate_data(
                data, schema_ver.content, validation_config
            )

            is_valid = len(validation_result['errors']) == 0
            status = 'valid' if is_valid else 'invalid'

            # Log validation
            validation_log = ValidationLog(
                schema_name=schema_name,
                schema_version=schema_version,
                filename=filename,
                validation_result=json.dumps(validation_result),
                is_valid=status
            )
            db.add(validation_log)
            await db.commit()
            await db.refresh(validation_log)

            return validation_result, is_valid, status

        except Exception as e:
            return {
                'errors': [{'message': f'Validation error: {str(e)}'}],
                'warnings': [],
                'summary': 'Validation failed'
            }, False, 'error'

    @staticmethod
    def _parse_csv(content: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Parse CSV content into list of dictionaries."""
        reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
        return list(reader)

    @staticmethod
    def _validate_data(
        data: Any,
        schema_content: str,
        validation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate data against a LinkML schema.

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        try:
            # Parse schema
            schema = yaml.safe_load(schema_content)

            # If data is a list of records (CSV), validate each row
            if isinstance(data, list):
                for idx, row in enumerate(data):
                    row_errors = ValidationService._validate_row(
                        row, schema, idx + 1, validation_config
                    )
                    errors.extend(row_errors)
            # If data is a single object
            elif isinstance(data, dict):
                errors.extend(ValidationService._validate_row(
                    data, schema, 1, validation_config
                ))
            else:
                errors.append({
                    'message': 'Data must be a dictionary or list of dictionaries',
                    'row': None,
                    'field': None
                })

            # Generate summary
            if errors:
                summary = f"Validation failed with {len(errors)} error(s)"
            elif warnings:
                summary = f"Validation passed with {len(warnings)} warning(s)"
            else:
                summary = "Validation passed successfully"

            return {
                'errors': errors,
                'warnings': warnings,
                'summary': summary
            }

        except Exception as e:
            return {
                'errors': [{'message': f'Schema validation error: {str(e)}', 'row': None, 'field': None}],
                'warnings': [],
                'summary': 'Validation failed'
            }

    @staticmethod
    def _validate_row(
        row: Dict[str, Any],
        schema: Dict[str, Any],
        row_number: int,
        validation_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Validate a single row against schema."""
        errors = []

        # Get schema slots/attributes
        slots = schema.get('slots', {})
        classes = schema.get('classes', {})

        # Basic validation: check required fields
        # This is a simplified validation - real LinkML validation is more complex
        for slot_name, slot_def in slots.items():
            if isinstance(slot_def, dict) and slot_def.get('required', False):
                if slot_name not in row or row[slot_name] in [None, '', 'NA']:
                    errors.append({
                        'message': f'Required field "{slot_name}" is missing or empty',
                        'row': row_number,
                        'field': slot_name
                    })

        # Type validation (basic)
        for field_name, field_value in row.items():
            if field_name in slots:
                slot_def = slots[field_name]
                if isinstance(slot_def, dict):
                    field_range = slot_def.get('range', 'string')

                    # Basic type checking
                    if field_range == 'integer':
                        try:
                            int(field_value)
                        except (ValueError, TypeError):
                            if field_value not in [None, '', 'NA']:
                                errors.append({
                                    'message': f'Field "{field_name}" should be an integer, got "{field_value}"',
                                    'row': row_number,
                                    'field': field_name
                                })
                    elif field_range == 'float':
                        try:
                            float(field_value)
                        except (ValueError, TypeError):
                            if field_value not in [None, '', 'NA']:
                                errors.append({
                                    'message': f'Field "{field_name}" should be a float, got "{field_value}"',
                                    'row': row_number,
                                    'field': field_name
                                })

        return errors

    @staticmethod
    async def get_validation_logs(
        db: AsyncSession,
        schema_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ValidationLog]:
        """Get validation logs, optionally filtered by schema name."""
        from sqlalchemy import select

        query = select(ValidationLog).order_by(ValidationLog.created_at.desc()).limit(limit)

        if schema_name:
            query = query.where(ValidationLog.schema_name == schema_name)

        result = await db.execute(query)
        return list(result.scalars().all())
