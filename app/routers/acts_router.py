from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional
import shutil
from pathlib import Path
from app.repository.acts_repo import Acts as ActsRepo
from app.services.acts_serv import Acts as ActsService
from app.services.import_scheduler import get_scheduler, ImportScheduler
from app.services.redis_service import RedisService
from app.schema.acts_dto import (
    ActsResponse, 
    ActsFilter, 
    ImportStatusResponse, 
    ImportTriggerResponse
)
from app.configs.dependencies import get_service_factory

actsRoutes = APIRouter(prefix="/acts", tags=["acts"])

# Dependency to get Redis service
def get_redis_service() -> RedisService:
    return RedisService()

# Dependency to get scheduler
def get_import_scheduler(redis_service: RedisService = Depends(get_redis_service)) -> ImportScheduler:
    return get_scheduler(redis_service)

# Service factory for Acts service
def acts_service_factory(
    scheduler: ImportScheduler = Depends(get_import_scheduler)
) -> ActsService:
    repo = ActsRepo()
    return ActsService(repo, scheduler)

@actsRoutes.post("/import", response_model=ImportTriggerResponse)
def trigger_import(service: ActsService = Depends(acts_service_factory)):
    """
    Trigger a manual import of Excel files from the /imports/ folder.
    This will scan for Excel files, parse them, and insert data into the acts table.
    """
    try:
        result = service.trigger_manual_import()
        return ImportTriggerResponse(
            message=result.get('message', 'Import triggered'),
            status=result.get('status', 'unknown'),
            job_id=result.get('job_id')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@actsRoutes.get("/import/status", response_model=ImportStatusResponse)
def get_import_status(service: ActsService = Depends(acts_service_factory)):
    """
    Get the status of the last import job.
    Returns information about when it ran, how many records were processed, etc.
    """
    try:
        return service.get_import_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@actsRoutes.get("/", response_model=dict)
def get_acts(
    state: Optional[str] = Query(None, description="Filter by state"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    legislative_area: Optional[str] = Query(None, description="Filter by legislative area"),
    employee_applicability: Optional[str] = Query(None, description="Filter by employee applicability"),
    search: Optional[str] = Query(None, description="Search in company_type, central_acts, and state_acts"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: ActsService = Depends(acts_service_factory)
):
    """
    Get acts with optional filters and pagination.
    
    Filters:
    - state: Filter by state
    - industry: Filter by industry sector
    - legislative_area: Filter by legislative area
    - employee_applicability: Filter by employee applicability
    - search: Search in company_type, central_acts, and state_acts
    
    Pagination:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (max 1000)
    """
    try:
        filters = ActsFilter(
            state=state,
            industry=industry,
            legislative_area=legislative_area,
            employee_applicability=employee_applicability,
            search=search,
            skip=skip,
            limit=limit
        )
        
        acts_list, total_count = service.get_acts_by_filters(filters)
        
        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "data": acts_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve acts: {str(e)}")

@actsRoutes.get("/filter-options", response_model=dict)
def get_filter_options(service: ActsService = Depends(acts_service_factory)):
    """
    Get available filter options (distinct values for states, industries, categories, statuses).
    Useful for populating filter dropdowns in the UI.
    """
    try:
        return service.get_filter_options()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")

@actsRoutes.get("/{act_id}", response_model=ActsResponse)
def get_act_by_id(
    act_id: int,
    service: ActsService = Depends(acts_service_factory)
):
    """
    Get a specific act by its ID.
    """
    try:
        return service.get_act_by_id(act_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve act: {str(e)}")

@actsRoutes.delete("/", response_model=dict)
def clear_all_acts(service: ActsService = Depends(acts_service_factory)):
    """
    Clear all acts from the database.
    WARNING: This is a destructive operation and should be used with caution.
    Typically used before a full refresh import.
    """
    try:
        return service.clear_all_acts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear acts: {str(e)}")

@actsRoutes.post("/upload", response_model=dict)
def upload_excel_file(
    file: UploadFile = File(...),
):
    """
    Upload an Excel file to the imports directory.
    The file will be picked up by the next import job.
    """
    try:
        # Validate file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
            
        imports_dir = Path("app/imports")
        imports_dir.mkdir(exist_ok=True, parents=True)
        
        file_path = imports_dir / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "message": f"File '{file.filename}' uploaded successfully",
            "path": str(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
