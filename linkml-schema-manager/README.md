# LinkML Schema Manager

A FastAPI-based LinkML schema manager, validator, and toolkit for managing and validating curated TSV/CSV files with LinkML schemas.

## Overview

This project provides a comprehensive API for:
- Managing LinkML schemas with versioning support
- Validating data files (CSV, TSV, YAML, JSON) against schemas using **LinkML's built-in validators**
- Generating code from schemas (Python, TypeScript, JSON Schema) using **LinkML's native generators**
- Creating Excel/CSV templates from schemas
- Tracking validation history with detailed logging

**Note:** This project leverages LinkML's powerful built-in functionality rather than custom YAML manipulation, ensuring compatibility with LinkML standards and access to all LinkML features.

## Features

### Schema Management
- **Upload schemas**: Store LinkML schemas with unique names
- **Version control**: Maintain multiple versions of each schema
- **Metadata tracking**: Capture creation dates, authors, and version notes
- **Schema validation**: Uses LinkML's SchemaView for proper schema validation
- **Diff generation**: Compare differences between schema versions

### Schema Functionality
- **Code generation**: Uses LinkML's official generators:
  - `PythonGenerator` for Python dataclasses
  - `TypescriptGenerator` for TypeScript interfaces
  - `JsonSchemaGenerator` for JSON Schema
- **Template generation**: Create CSV templates using SchemaView for proper schema introspection
- **Multiple formats**: Support for various output formats

### Validation
- **File validation**: Uses LinkML's Validator for proper schema-based validation of CSV, TSV, YAML, and JSON files
- **Detailed reports**: Get comprehensive validation results with errors and warnings
- **Validation history**: Track all validation attempts with timestamps
- **Configurable validation**: Optional validation configuration (e.g., target class selection)

### Logging
- **Request/Response logging**: Comprehensive logging of all API interactions
- **Performance tracking**: Measure request processing time
- **Error tracking**: Detailed error logs for debugging

## Installation

### Using uv (recommended)

```bash
cd linkml-schema-manager
uv pip install -e .
```

### Using pip

```bash
cd linkml-schema-manager
pip install -e .
```

## Running the Application

### Development Server

```bash
cd linkml-schema-manager
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
cd linkml-schema-manager
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI specification**: http://localhost:8000/openapi.json

## API Endpoints

### Schema Management

#### Create a Schema
```bash
POST /schemas/
Content-Type: application/json

{
  "name": "sample_schema",
  "description": "Schema for sample data"
}
```

#### List All Schemas
```bash
GET /schemas/
```

#### Get Schema Details
```bash
GET /schemas/{schema_name}
```

#### Delete Schema
```bash
DELETE /schemas/{schema_name}
```

#### Upload Schema Version
```bash
POST /schemas/{schema_name}/versions
Content-Type: multipart/form-data

- version: "1.0.0"
- notes: "Initial version"
- created_by: "user@example.com"
- file: schema.yaml
```

#### List Schema Versions
```bash
GET /schemas/{schema_name}/versions
```

#### Get Specific Version
```bash
GET /schemas/{schema_name}/versions/{version}
```

#### Compare Schema Versions
```bash
POST /schemas/{schema_name}/diff
Content-Type: application/json

{
  "schema_name": "sample_schema",
  "version1": "1.0.0",
  "version2": "1.1.0"
}
```

### Code Generation

#### Generate Code (Generic)
```bash
POST /codegen/generate
Content-Type: application/json

{
  "schema_name": "sample_schema",
  "schema_version": "1.0.0",
  "language": "python",
  "options": {}
}
```

#### Generate Python Classes
```bash
GET /codegen/{schema_name}/{version}/python
```

#### Generate TypeScript Interfaces
```bash
GET /codegen/{schema_name}/{version}/typescript
```

#### Generate JSON Schema
```bash
GET /codegen/{schema_name}/{version}/json-schema
```

#### Generate Excel Template
```bash
GET /codegen/{schema_name}/{version}/excel-template
```

### Validation

#### Validate Data File
```bash
POST /validate/
Content-Type: multipart/form-data

- schema_name: "sample_schema"
- schema_version: "1.0.0"
- file: data.csv
- validation_config: "{}"  # Optional JSON string
```

#### Get Validation Logs
```bash
GET /validate/logs?schema_name=sample_schema&limit=100
```

#### Get Specific Validation Log
```bash
GET /validate/logs/{validation_id}
```

## Example Workflow

### 1. Create a Schema
```bash
curl -X POST "http://localhost:8000/schemas/" \
  -H "Content-Type: application/json" \
  -d '{"name": "patient_data", "description": "Schema for patient records"}'
```

### 2. Upload a Schema Version
```bash
curl -X POST "http://localhost:8000/schemas/patient_data/versions" \
  -F "version=1.0.0" \
  -F "notes=Initial version" \
  -F "created_by=researcher@example.com" \
  -F "file=@patient_schema.yaml"
```

### 3. Validate a Data File
```bash
curl -X POST "http://localhost:8000/validate/" \
  -F "schema_name=patient_data" \
  -F "schema_version=1.0.0" \
  -F "file=@patient_data.csv"
```

### 4. Generate Python Code
```bash
curl "http://localhost:8000/codegen/patient_data/1.0.0/python" \
  -o patient_models.py
```

## Project Structure

```
linkml-schema-manager/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database setup and session management
│   ├── models.py               # SQLAlchemy database models
│   ├── schemas.py              # Pydantic schemas for validation
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── schemas.py          # Schema management endpoints
│   │   ├── codegen.py          # Code generation endpoints
│   │   └── validation.py       # Validation endpoints
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── schema_service.py   # Schema management logic
│   │   ├── validation_service.py  # Validation logic
│   │   └── codegen_service.py  # Code generation logic
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── logging_middleware.py  # Request/response logging
├── schema_storage/             # Directory for stored schema files (auto-created)
├── schemas.db                  # SQLite database (auto-created)
├── app.log                     # Application logs (auto-created)
├── pyproject.toml             # Project dependencies
└── README.md                   # This file
```

## Database Models

### Schema
- **id**: Primary key
- **name**: Unique schema name
- **description**: Optional description
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp

### SchemaVersion
- **id**: Primary key
- **schema_id**: Foreign key to Schema
- **version**: Version identifier
- **content**: YAML content
- **file_path**: Path to stored file
- **created_at**: Creation timestamp
- **created_by**: Optional creator identifier
- **notes**: Optional version notes

### ValidationLog
- **id**: Primary key
- **schema_name**: Schema name used
- **schema_version**: Version used
- **filename**: Validated file name
- **validation_result**: JSON validation results
- **is_valid**: Validation status (valid/invalid/error)
- **created_at**: Validation timestamp

## Configuration

Environment variables can be used to configure the application:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `SCHEMA_STORAGE_DIR`: Directory for storing schema files
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE`: Path to log file

## Development

### Running Tests
```bash
cd linkml-schema-manager
pytest
```

### Code Style
The project follows standard Python conventions with:
- Type hints for function parameters and returns
- Docstrings for classes and functions
- Async/await patterns for database operations

## LinkML Schema Format

Schemas should follow the LinkML specification. Example:

```yaml
id: https://example.org/sample
name: sample
description: Sample schema for patient data

slots:
  patient_id:
    required: true
    range: string
    description: Unique patient identifier

  age:
    required: true
    range: integer
    description: Patient age in years

  diagnosis:
    required: false
    range: string
    description: Primary diagnosis

classes:
  Patient:
    description: Patient record
    attributes:
      patient_id:
        required: true
      age:
        required: true
      diagnosis:
        required: false
```

## Future Enhancements

Potential improvements:
- User authentication and authorization
- Batch validation of multiple files
- Webhook notifications for validation results
- Schema inheritance and composition
- Advanced validation rules and custom validators
- Integration with external schema registries
- Real-time validation via WebSocket
- Export validation reports in multiple formats (PDF, HTML)

## License

This project is part of the code-research repository.

## Support

For issues, questions, or contributions, please refer to the main repository documentation.
