from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, File, UploadFile
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
# from app.auth.auth import auth_wrapper  # Removed unused and invalid import
from app.services.monthly_updates_serv import MonthlyUpdates
from app.services.monthly_updates_scheduler import MonthlyUpdatesImportScheduler
from app.services.redis_service import RedisService
from app.repository.monthly_updates_repo import MonthlyUpdates as MonthlyUpdatesRepo
from app.schema.monthly_updates_dto import (
    MonthlyUpdateFilter, 
    MonthlyUpdateResponse, 
    ImportStatusResponse, 
    ImportTriggerResponse
)

# Initialize services
# In a real app we'd use dependency injection properly, but here we instantiate for simplicity
# similar to other routers in this project
redis_service = RedisService()
scheduler = MonthlyUpdatesImportScheduler(redis_service)
repo = MonthlyUpdatesRepo()
service = MonthlyUpdates(repo, scheduler)

monthlyUpdatesRoutes = APIRouter(
    prefix="/monthly-updates",
    tags=["Monthly Updates"]
)

@monthlyUpdatesRoutes.get("/", response_model=List[MonthlyUpdateResponse])
def get_monthly_updates(
    category: Optional[str] = Query(None, description="Filter by category"),
    state: Optional[str] = Query(None, description="Filter by state"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    search: Optional[str] = Query(None, description="Search term"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    # user = Depends(auth_wrapper)  # Optional: secure if needed
):
    """
    Get all monthly updates with optional filters.
    """
    filters = MonthlyUpdateFilter(
        category=category,
        state=state,
        change_type=change_type,
        search=search,
        skip=skip,
        limit=limit
    )
    updates, total = service.get_updates_by_filters(filters)
    # We could return a paginated response wrapper, but list is fine for now
    return updates

@monthlyUpdatesRoutes.get("/daily", response_model=List[Dict[str, Any]])
def get_daily_updates(limit: int = Query(5, ge=1, le=20)):
    """
    Get latest updates specifically for the Daily Updates widget.
    Returns a simplified list of dicts.
    """
    return service.get_daily_updates(limit=limit)

@monthlyUpdatesRoutes.get("/recent", response_model=List[Dict[str, Any]])
def get_recent_updates(days: int = Query(30, ge=1)):
    """
    Get updates from the last N days.
    """
    return service.get_recent_updates(days=days)

@monthlyUpdatesRoutes.post("/import", response_model=ImportTriggerResponse)
async def import_monthly_updates(file: UploadFile = File(...)):
    """
    Import Monthly Updates from Excel file.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)")
    
    content = await file.read()
    result = service.import_excel_file(content, file.filename)
    return result

@monthlyUpdatesRoutes.get("/import/status", response_model=ImportStatusResponse)
def get_import_status():
    """
    Check the status of the import job.
    """
    return service.get_import_status()

@monthlyUpdatesRoutes.get("/filters", response_model=Dict[str, List[str]])
def get_filters():
    """
    Get available filter options (categories, states, etc.)
    """
    return service.get_filter_options()

@monthlyUpdatesRoutes.delete("/")
def clear_all_updates():
    """
    Clear all monthly updates (for admin/testing).
    """
    return service.clear_all_updates()
