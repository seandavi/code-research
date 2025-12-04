"""Service for code generation from LinkML schemas."""
import yaml
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.schema_service import SchemaService


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
        """Generate Python dataclasses from LinkML schema."""
        try:
            schema = yaml.safe_load(schema_content)

            code_lines = [
                '"""Auto-generated Python classes from LinkML schema."""',
                'from dataclasses import dataclass, field',
                'from typing import Optional, List, Dict, Any',
                'from datetime import datetime',
                '',
                ''
            ]

            # Generate classes
            classes = schema.get('classes', {})
            for class_name, class_def in classes.items():
                code_lines.append(f'@dataclass')
                code_lines.append(f'class {class_name}:')

                # Get class description
                if isinstance(class_def, dict) and 'description' in class_def:
                    code_lines.append(f'    """{class_def["description"]}"""')

                # Get class attributes
                attributes = class_def.get('attributes', {}) if isinstance(class_def, dict) else {}
                if not attributes:
                    code_lines.append('    pass')
                else:
                    for attr_name, attr_def in attributes.items():
                        if isinstance(attr_def, dict):
                            attr_type = CodeGenService._get_python_type(attr_def.get('range', 'string'))
                            required = attr_def.get('required', False)

                            if required:
                                code_lines.append(f'    {attr_name}: {attr_type}')
                            else:
                                code_lines.append(f'    {attr_name}: Optional[{attr_type}] = None')

                code_lines.append('')

            return {
                'code': '\n'.join(code_lines),
                'language': 'python',
                'files': {'models.py': '\n'.join(code_lines)}
            }

        except Exception as e:
            return {
                'error': f'Failed to generate Python code: {str(e)}',
                'code': ''
            }

    @staticmethod
    def _generate_typescript(schema_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate TypeScript interfaces from LinkML schema."""
        try:
            schema = yaml.safe_load(schema_content)

            code_lines = [
                '// Auto-generated TypeScript interfaces from LinkML schema',
                '',
            ]

            # Generate interfaces
            classes = schema.get('classes', {})
            for class_name, class_def in classes.items():
                # Get class description
                if isinstance(class_def, dict) and 'description' in class_def:
                    code_lines.append(f'/** {class_def["description"]} */')

                code_lines.append(f'export interface {class_name} {{')

                # Get class attributes
                attributes = class_def.get('attributes', {}) if isinstance(class_def, dict) else {}
                for attr_name, attr_def in attributes.items():
                    if isinstance(attr_def, dict):
                        attr_type = CodeGenService._get_typescript_type(attr_def.get('range', 'string'))
                        required = attr_def.get('required', False)
                        optional = '?' if not required else ''

                        if 'description' in attr_def:
                            code_lines.append(f'  /** {attr_def["description"]} */')
                        code_lines.append(f'  {attr_name}{optional}: {attr_type};')

                code_lines.append('}')
                code_lines.append('')

            return {
                'code': '\n'.join(code_lines),
                'language': 'typescript',
                'files': {'types.ts': '\n'.join(code_lines)}
            }

        except Exception as e:
            return {
                'error': f'Failed to generate TypeScript code: {str(e)}',
                'code': ''
            }

    @staticmethod
    def _generate_json_schema(schema_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate JSON Schema from LinkML schema."""
        try:
            import json
            schema = yaml.safe_load(schema_content)

            json_schema = {
                '$schema': 'http://json-schema.org/draft-07/schema#',
                'title': schema.get('name', schema.get('id', 'Schema')),
                'description': schema.get('description', ''),
                'type': 'object',
                'properties': {},
                'required': []
            }

            # Convert slots to JSON schema properties
            slots = schema.get('slots', {})
            for slot_name, slot_def in slots.items():
                if isinstance(slot_def, dict):
                    prop = {
                        'type': CodeGenService._get_json_schema_type(slot_def.get('range', 'string'))
                    }
                    if 'description' in slot_def:
                        prop['description'] = slot_def['description']

                    json_schema['properties'][slot_name] = prop

                    if slot_def.get('required', False):
                        json_schema['required'].append(slot_name)

            return {
                'code': json.dumps(json_schema, indent=2),
                'language': 'json-schema',
                'files': {'schema.json': json.dumps(json_schema, indent=2)}
            }

        except Exception as e:
            return {
                'error': f'Failed to generate JSON Schema: {str(e)}',
                'code': ''
            }

    @staticmethod
    def _get_python_type(linkml_type: str) -> str:
        """Map LinkML type to Python type."""
        type_map = {
            'string': 'str',
            'integer': 'int',
            'float': 'float',
            'double': 'float',
            'boolean': 'bool',
            'date': 'str',
            'datetime': 'datetime',
            'uri': 'str',
        }
        return type_map.get(linkml_type.lower(), 'Any')

    @staticmethod
    def _get_typescript_type(linkml_type: str) -> str:
        """Map LinkML type to TypeScript type."""
        type_map = {
            'string': 'string',
            'integer': 'number',
            'float': 'number',
            'double': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'uri': 'string',
        }
        return type_map.get(linkml_type.lower(), 'any')

    @staticmethod
    def _get_json_schema_type(linkml_type: str) -> str:
        """Map LinkML type to JSON Schema type."""
        type_map = {
            'string': 'string',
            'integer': 'integer',
            'float': 'number',
            'double': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'uri': 'string',
        }
        return type_map.get(linkml_type.lower(), 'string')

    @staticmethod
    async def generate_excel_template(
        db: AsyncSession,
        schema_name: str,
        schema_version: str
    ) -> Optional[bytes]:
        """
        Generate an Excel template from a schema.

        Returns:
            Excel file as bytes or None if schema not found
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

            schema = yaml.safe_load(schema_ver.content)

            # Create CSV template (simplified - could use openpyxl for real Excel)
            output = io.StringIO()

            # Get column headers from slots
            slots = schema.get('slots', {})
            headers = list(slots.keys())

            writer = csv.writer(output)
            writer.writerow(headers)

            # Add example row with placeholders
            example_row = []
            for slot_name, slot_def in slots.items():
                if isinstance(slot_def, dict):
                    slot_range = slot_def.get('range', 'string')
                    if slot_range == 'integer':
                        example_row.append('0')
                    elif slot_range == 'float':
                        example_row.append('0.0')
                    elif slot_range == 'boolean':
                        example_row.append('true')
                    else:
                        example_row.append(f'example_{slot_name}')
                else:
                    example_row.append(f'example_{slot_name}')

            writer.writerow(example_row)

            return output.getvalue().encode('utf-8')

        except Exception as e:
            return None
