"""API routes for code generation and schema functionality."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CodeGenerationRequest, CodeGenerationResponse
from app.services.codegen_service import CodeGenService

router = APIRouter(prefix="/codegen", tags=["code-generation"])


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(
    request: CodeGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate code from a schema in the specified language."""
    result = await CodeGenService.generate_code(
        db,
        request.schema_name,
        request.schema_version,
        request.language,
        request.options
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Schema {request.schema_name} version {request.schema_version} not found"
        )

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return CodeGenerationResponse(
        schema_name=request.schema_name,
        schema_version=request.schema_version,
        language=request.language,
        code=result['code'],
        files=result.get('files')
    )


@router.get("/{schema_name}/{version}/python")
async def generate_python(
    schema_name: str,
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate Python code from a schema."""
    result = await CodeGenService.generate_code(
        db, schema_name, version, 'python'
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Schema {schema_name} version {version} not found"
        )

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return Response(content=result['code'], media_type='text/plain')


@router.get("/{schema_name}/{version}/typescript")
async def generate_typescript(
    schema_name: str,
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate TypeScript code from a schema."""
    result = await CodeGenService.generate_code(
        db, schema_name, version, 'typescript'
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Schema {schema_name} version {version} not found"
        )

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return Response(content=result['code'], media_type='text/plain')


@router.get("/{schema_name}/{version}/json-schema")
async def generate_json_schema(
    schema_name: str,
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate JSON Schema from a LinkML schema."""
    result = await CodeGenService.generate_code(
        db, schema_name, version, 'json-schema'
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Schema {schema_name} version {version} not found"
        )

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return Response(content=result['code'], media_type='application/json')


@router.get("/{schema_name}/{version}/excel-template")
async def generate_excel_template(
    schema_name: str,
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate an Excel template from a schema."""
    result = await CodeGenService.generate_excel_template(
        db, schema_name, version
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Schema {schema_name} version {version} not found or generation failed"
        )

    return Response(
        content=result,
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{schema_name}_v{version}_template.csv"'}
    )
