from typing import List, Dict, Any
from app.repository.monthly_updates_repo import MonthlyUpdates as MonthlyUpdatesRepo
from app.schema.monthly_updates_dto import MonthlyUpdateFilter, MonthlyUpdateResponse, ImportStatusResponse
from app.services.monthly_updates_scheduler import MonthlyUpdatesImportScheduler

class MonthlyUpdates:
    """Service layer for Monthly Updates business logic"""
    
    def __init__(self, repo: MonthlyUpdatesRepo, scheduler: MonthlyUpdatesImportScheduler):
        self.repo = repo
        self.scheduler = scheduler

    def trigger_manual_import(self) -> Dict[str, Any]:
        """Trigger a manual import job (Deprecated in favor of upload)"""
        return self.scheduler.trigger_manual_import()

    def import_excel_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Import Excel file from bytes"""
        success, message, count = self.scheduler.excel_service.process_excel_stream(file_content, filename)
        return {
            "status": "completed" if success else "failed",
            "message": message,
            "records_processed": count,
            "job_id": None
        }

    def get_import_status(self) -> ImportStatusResponse:
        """Get the current import job status"""
        status_data = self.scheduler.get_job_status()
        return ImportStatusResponse(**status_data)

    def get_updates_by_filters(self, filters: MonthlyUpdateFilter) -> tuple[List[MonthlyUpdateResponse], int]:
        """
        Get monthly updates with filters and pagination.
        Returns (list of updates, total count)
        """
        updates_list, total_count = self.repo.find_by_filters(filters)
        
        # Convert to response DTOs
        updates_response = [MonthlyUpdateResponse.model_validate(update) for update in updates_list]
        
        return updates_response, total_count

    def get_update_by_id(self, update_id: int) -> MonthlyUpdateResponse:
        """Get a specific monthly update by ID"""
        update = self.repo.find_by_id(update_id)
        if not update:
            raise ValueError(f"Monthly update with ID {update_id} not found")
        
        return MonthlyUpdateResponse.model_validate(update)

    def clear_all_updates(self) -> Dict[str, str]:
        """Clear all monthly updates from the database (admin operation)"""
        self.repo.truncate_table()
        return {"message": "All monthly updates have been cleared"}

    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options for dropdowns"""
        return {
            'categories': self.repo.get_distinct_values('category'),
            'states': self.repo.get_distinct_values('state'),
            'change_types': self.repo.get_distinct_values('change_type')
        }
    
    def get_recent_updates(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent updates from the last N days"""
        return self.repo.find_recent_updates(days=days)
    
    def get_daily_updates(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the latest N updates for daily updates widget"""
        # Use find_by_filters with limit and sort by update_date desc
        filters = MonthlyUpdateFilter(skip=0, limit=limit)
        updates_list, _ = self.repo.find_by_filters(filters)
        
        # Convert SQLAlchemy objects to dicts
        result = []
        for update in updates_list:
            if hasattr(update, '__dict__'):
                update_dict = {
                    'id': update.id,
                    'title': update.title,
                    'category': update.category,
                    'description': update.description,
                    'change_type': update.change_type,
                    'state': update.state,
                    'effective_date': update.effective_date.isoformat() if update.effective_date else None,
                    'update_date': update.update_date.isoformat() if update.update_date else None,
                    'source_link': update.source_link
                }
                result.append(update_dict)
        
        return result

