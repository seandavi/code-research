"""Service for schema management operations."""
import os
import yaml
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Schema, SchemaVersion
from app.config import SCHEMA_STORAGE_DIR
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.dumpers import yaml_dumper
from linkml.validator import validate


class SchemaService:
    """Service for managing LinkML schemas."""

    @staticmethod
    async def create_schema(
        db: AsyncSession,
        name: str,
        description: Optional[str] = None
    ) -> Schema:
        """Create a new schema."""
        schema = Schema(name=name, description=description)
        db.add(schema)
        await db.commit()
        await db.refresh(schema)
        return schema

    @staticmethod
    async def get_schema(db: AsyncSession, schema_id: int) -> Optional[Schema]:
        """Get a schema by ID."""
        result = await db.execute(
            select(Schema).where(Schema.id == schema_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_schema_by_name(db: AsyncSession, name: str) -> Optional[Schema]:
        """Get a schema by name."""
        result = await db.execute(
            select(Schema).where(Schema.name == name).options(selectinload(Schema.versions))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_schemas(db: AsyncSession) -> List[Schema]:
        """List all schemas."""
        result = await db.execute(select(Schema))
        return list(result.scalars().all())

    @staticmethod
    async def delete_schema(db: AsyncSession, schema_id: int) -> bool:
        """Delete a schema and all its versions."""
        schema = await SchemaService.get_schema(db, schema_id)
        if not schema:
            return False
        await db.delete(schema)
        await db.commit()
        return True

    @staticmethod
    def validate_yaml_content(content: str) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Validate YAML content and check if it's a valid LinkML schema.

        Returns:
            Tuple of (is_valid, error_message, parsed_content)
        """
        try:
            # Parse YAML
            parsed = yaml.safe_load(content)

            if not isinstance(parsed, dict):
                return False, "YAML content must be a dictionary", None

            # Basic LinkML schema validation - check for required fields
            if 'id' not in parsed and 'name' not in parsed:
                return False, "LinkML schema must have 'id' or 'name' field", None

            # Try to validate as LinkML schema
            # This is a basic check - more sophisticated validation could be added
            return True, None, parsed

        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {str(e)}", None
        except Exception as e:
            return False, f"Validation error: {str(e)}", None

    @staticmethod
    async def create_schema_version(
        db: AsyncSession,
        schema_id: int,
        version: str,
        content: str,
        created_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[SchemaVersion], Optional[str]]:
        """
        Create a new version of a schema.

        Returns:
            Tuple of (schema_version, error_message)
        """
        # Validate YAML content
        is_valid, error_msg, parsed = SchemaService.validate_yaml_content(content)
        if not is_valid:
            return None, error_msg

        # Create storage directory for this schema
        schema = await SchemaService.get_schema(db, schema_id)
        if not schema:
            return None, "Schema not found"

        schema_dir = SCHEMA_STORAGE_DIR / schema.name
        schema_dir.mkdir(exist_ok=True, parents=True)

        # Save file
        file_path = schema_dir / f"v{version}.yaml"
        with open(file_path, 'w') as f:
            f.write(content)

        # Create version record
        schema_version = SchemaVersion(
            schema_id=schema_id,
            version=version,
            content=content,
            file_path=str(file_path),
            created_by=created_by,
            notes=notes
        )
        db.add(schema_version)

        try:
            await db.commit()
            await db.refresh(schema_version)
            return schema_version, None
        except Exception as e:
            await db.rollback()
            # Clean up file if database insert failed
            if file_path.exists():
                file_path.unlink()
            return None, f"Error creating version: {str(e)}"

    @staticmethod
    async def get_schema_version(
        db: AsyncSession,
        schema_name: str,
        version: str
    ) -> Optional[SchemaVersion]:
        """Get a specific version of a schema."""
        result = await db.execute(
            select(SchemaVersion)
            .join(Schema)
            .where(Schema.name == schema_name, SchemaVersion.version == version)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_schema_versions(
        db: AsyncSession,
        schema_id: int
    ) -> List[SchemaVersion]:
        """List all versions of a schema."""
        result = await db.execute(
            select(SchemaVersion)
            .where(SchemaVersion.schema_id == schema_id)
            .order_by(SchemaVersion.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def get_schema_diff(content1: str, content2: str) -> Tuple[str, dict]:
        """
        Generate a diff between two schema versions.

        Returns:
            Tuple of (unified_diff, changes_summary)
        """
        import difflib

        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)

        diff = ''.join(difflib.unified_diff(
            lines1, lines2,
            fromfile='version1',
            tofile='version2',
            lineterm=''
        ))

        # Parse changes summary
        parsed1 = yaml.safe_load(content1)
        parsed2 = yaml.safe_load(content2)

        changes_summary = {
            'added_fields': [],
            'removed_fields': [],
            'modified_fields': [],
            'total_changes': 0
        }

        # Simple comparison of top-level keys
        if isinstance(parsed1, dict) and isinstance(parsed2, dict):
            keys1 = set(parsed1.keys())
            keys2 = set(parsed2.keys())

            changes_summary['added_fields'] = list(keys2 - keys1)
            changes_summary['removed_fields'] = list(keys1 - keys2)

            for key in keys1 & keys2:
                if parsed1[key] != parsed2[key]:
                    changes_summary['modified_fields'].append(key)

            changes_summary['total_changes'] = (
                len(changes_summary['added_fields']) +
                len(changes_summary['removed_fields']) +
                len(changes_summary['modified_fields'])
            )

        return diff, changes_summary
