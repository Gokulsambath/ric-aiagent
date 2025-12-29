from typing import List, Dict, Any
from app.repository.acts_repo import Acts as ActsRepo
from app.schema.acts_dto import ActsFilter, ActsResponse, ImportStatusResponse
from app.services.import_scheduler import ImportScheduler

class Acts:
    """Service layer for Acts business logic"""
    
    def __init__(self, repo: ActsRepo, scheduler: ImportScheduler):
        self.repo = repo
        self.scheduler = scheduler

    def trigger_manual_import(self) -> Dict[str, Any]:
        """Trigger a manual import job"""
        return self.scheduler.trigger_manual_import()

    def get_import_status(self) -> ImportStatusResponse:
        """Get the current import job status"""
        status_data = self.scheduler.get_job_status()
        return ImportStatusResponse(**status_data)

    def get_acts_by_filters(self, filters: ActsFilter) -> tuple[List[ActsResponse], int]:
        """
        Get acts with filters and pagination.
        Returns (list of acts, total count)
        """
        acts_list, total_count = self.repo.find_by_filters(filters)
        
        # Convert to response DTOs
        acts_response = [ActsResponse.model_validate(act) for act in acts_list]
        
        return acts_response, total_count

    def get_act_by_id(self, act_id: int) -> ActsResponse:
        """Get a specific act by ID"""
        act = self.repo.find_by_id(act_id)
        if not act:
            raise ValueError(f"Act with ID {act_id} not found")
        
        return ActsResponse.model_validate(act)

    def clear_all_acts(self) -> Dict[str, str]:
        """Clear all acts from the database (admin operation)"""
        self.repo.truncate_table()
        return {"message": "All acts have been cleared"}

    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options for dropdowns"""
        return {
            'states': self.repo.get_distinct_values('state'),
            'industries': self.repo.get_distinct_values('industry'),
            'legislative_areas': self.repo.get_distinct_values('legislative_area'),
            'employee_applicabilities': self.repo.get_distinct_values('employee_applicability')
        }
