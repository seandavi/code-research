"""Service for code generation from LinkML schemas."""
import yaml
import tempfile
import os
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.schema_service import SchemaService
from linkml.generators.pythongen import PythonGenerator
from linkml.generators.typescriptgen import TypescriptGenerator
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime.utils.schemaview import SchemaView


class CodeGenService:
    """Service for generating code and artifacts from LinkML schemas."""

    @staticmethod
    async def generate_code(
        db: AsyncSession,
        schema_name: str,
        schema_version: str,
        language: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate code from a schema.

        Returns:
            Dictionary with generated code or None if schema not found
        """
        # Get schema version
        schema_ver = await SchemaService.get_schema_version(
            db, schema_name, schema_version
        )

        if not schema_ver:
            return None

        # Generate code based on language
        if language.lower() == 'python':
            return CodeGenService._generate_python(schema_ver.content, options)
        elif language.lower() == 'typescript':
            return CodeGenService._generate_typescript(schema_ver.content, options)
        elif language.lower() == 'json-schema':
            return CodeGenService._generate_json_schema(schema_ver.content, options)
        else:
            return {
                'error': f'Unsupported language: {language}',
                'code': ''
            }

    @staticmethod
    def _generate_python(schema_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate Python dataclasses from LinkML schema using LinkML's PythonGenerator."""
        try:
            # Write schema to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                tmp.write(schema_content)
                tmp_path = tmp.name

            try:
                # Use LinkML's PythonGenerator
                generator = PythonGenerator(tmp_path, **(options or {}))
                generated_code = generator.serialize()

                return {
                    'code': generated_code,
                    'language': 'python',
                    'files': {'models.py': generated_code}
                }
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return {
                'error': f'Failed to generate Python code: {str(e)}',
                'code': ''
            }

    @staticmethod
    def _generate_typescript(schema_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate TypeScript interfaces from LinkML schema using LinkML's TypescriptGenerator."""
        try:
            # Write schema to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                tmp.write(schema_content)
                tmp_path = tmp.name

            try:
                # Use LinkML's TypescriptGenerator
                generator = TypescriptGenerator(tmp_path, **(options or {}))
                generated_code = generator.serialize()

                return {
                    'code': generated_code,
                    'language': 'typescript',
                    'files': {'types.ts': generated_code}
                }
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return {
                'error': f'Failed to generate TypeScript code: {str(e)}',
                'code': ''
            }

    @staticmethod
    def _generate_json_schema(schema_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate JSON Schema from LinkML schema using LinkML's JsonSchemaGenerator."""
        try:
            # Write schema to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                tmp.write(schema_content)
                tmp_path = tmp.name

            try:
                # Use LinkML's JsonSchemaGenerator
                generator = JsonSchemaGenerator(tmp_path, **(options or {}))
                generated_code = generator.serialize()

                return {
                    'code': generated_code,
                    'language': 'json-schema',
                    'files': {'schema.json': generated_code}
                }
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return {
                'error': f'Failed to generate JSON Schema: {str(e)}',
                'code': ''
            }

    @staticmethod
    async def generate_excel_template(
        db: AsyncSession,
        schema_name: str,
        schema_version: str
    ) -> Optional[bytes]:
        """
        Generate an Excel template from a schema using SchemaView.

        Returns:
            CSV file as bytes or None if schema not found
        """
        # Get schema version
        schema_ver = await SchemaService.get_schema_version(
            db, schema_name, schema_version
        )

        if not schema_ver:
            return None

        try:
            import io
            import csv

            # Write schema to temporary file for SchemaView
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                tmp.write(schema_ver.content)
                tmp_path = tmp.name

            try:
                # Use SchemaView for proper schema introspection
                schema_view = SchemaView(tmp_path)

                # Create CSV template
                output = io.StringIO()

                # Get all slots from the schema
                all_slots = schema_view.all_slots()
                headers = [slot.name for slot in all_slots.values() if slot.name]

                writer = csv.writer(output)
                writer.writerow(headers)

                # Add example row with placeholders based on slot ranges
                example_row = []
                for slot in all_slots.values():
                    if not slot.name:
                        continue

                    slot_range = slot.range or 'string'

                    if slot_range == 'integer':
                        example_row.append('0')
                    elif slot_range in ['float', 'double']:
                        example_row.append('0.0')
                    elif slot_range == 'boolean':
                        example_row.append('true')
                    elif slot_range == 'date':
                        example_row.append('2024-01-01')
                    elif slot_range == 'datetime':
                        example_row.append('2024-01-01T00:00:00')
                    else:
                        example_row.append(f'example_{slot.name}')

                writer.writerow(example_row)

                return output.getvalue().encode('utf-8')

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return None
