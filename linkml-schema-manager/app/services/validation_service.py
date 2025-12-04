"""Service for data validation operations."""
import json
import csv
import yaml
import tempfile
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ValidationLog, SchemaVersion
from app.services.schema_service import SchemaService
from linkml.validator import Validator
from linkml_runtime.utils.schemaview import SchemaView


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
        Validate data against a LinkML schema using LinkML's Validator.

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        try:
            # Write schema to temporary file for LinkML validator
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as schema_tmp:
                schema_tmp.write(schema_content)
                schema_path = schema_tmp.name

            try:
                # Create SchemaView for schema introspection
                schema_view = SchemaView(schema_path)

                # Get the target class for validation
                # Use the first class defined in the schema, or allow config to override
                target_class = None
                if validation_config and 'target_class' in validation_config:
                    target_class = validation_config['target_class']
                else:
                    # Get first class from schema
                    all_classes = schema_view.all_classes()
                    if all_classes:
                        target_class = list(all_classes.keys())[0]

                # Create validator
                validator = Validator(schema_path)

                # Validate data
                if isinstance(data, list):
                    # Validate each row
                    for idx, row in enumerate(data):
                        row_errors = ValidationService._validate_single_instance(
                            validator, row, target_class, idx + 1
                        )
                        errors.extend(row_errors)
                elif isinstance(data, dict):
                    # Validate single object
                    errors.extend(ValidationService._validate_single_instance(
                        validator, data, target_class, 1
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

            finally:
                os.unlink(schema_path)

        except Exception as e:
            return {
                'errors': [{'message': f'Schema validation error: {str(e)}', 'row': None, 'field': None}],
                'warnings': [],
                'summary': 'Validation failed'
            }

    @staticmethod
    def _validate_single_instance(
        validator: Validator,
        instance: Dict[str, Any],
        target_class: Optional[str],
        row_number: int
    ) -> List[Dict[str, Any]]:
        """Validate a single instance using LinkML's validator."""
        errors = []

        try:
            # Use LinkML's validator to validate the instance
            validation_report = validator.validate(instance, target_class=target_class)

            # Convert validation report to our error format
            if validation_report and hasattr(validation_report, 'results'):
                for result in validation_report.results:
                    if result.severity in ['ERROR', 'FATAL']:
                        errors.append({
                            'message': result.message,
                            'row': row_number,
                            'field': getattr(result, 'field', None)
                        })
            # If validation failed but no specific results, just note it
            elif validation_report is not None:
                # Validation passed
                pass

        except Exception as e:
            # If LinkML validation fails, capture the error
            errors.append({
                'message': f'Validation error: {str(e)}',
                'row': row_number,
                'field': None
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
