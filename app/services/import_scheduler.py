import logging
from datetime import datetime
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.services.excel_import_service import ExcelImportService
from app.repository.acts_repo import Acts as ActsRepo
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

class ImportScheduler:
    """Background scheduler for periodic Excel imports"""
    
    def __init__(self, redis_service: RedisService):
        self.scheduler = BackgroundScheduler()
        self.excel_service = ExcelImportService()
        self.acts_repo = ActsRepo()
        self.redis_service = redis_service
        self.job_status_key = "import_job_status"
        
    def start_scheduler(self, interval_minutes: int = 5):
        """
        Start the background scheduler with specified interval.
        Default: every 5 minutes
        """
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Add job with interval trigger
            self.scheduler.add_job(
                func=self.run_import_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='excel_import_job',
                name='Excel Import Job',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info(f"Import scheduler started with {interval_minutes} minute interval")
        except Exception as e:
            logger.error(f"Failed to start import scheduler: {str(e)}")
            # Don't re-raise the exception to avoid crashing the application
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Import scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    def run_import_job(self) -> Dict[str, Any]:
        """
        Execute the import job.
        Scans for Excel files and imports them.
        """
        job_start = datetime.now()
        
        try:
            # Update status to running
            self._update_job_status({
                'status': 'running',
                'message': 'Import job started',
                'last_run': job_start.isoformat(),
                'records_processed': 0,
                'records_failed': 0
            })
            
            # Scan for Excel files
            excel_files = self.excel_service.scan_imports_folder()
            
            if not excel_files:
                logger.info("No Excel files found to import")
                self._update_job_status({
                    'status': 'idle',
                    'message': 'No files to import',
                    'last_run': job_start.isoformat()
                })
                return {'status': 'idle', 'message': 'No files to import'}
            
            total_processed = 0
            total_failed = 0
            
            # Process each file
            for file_path in excel_files:
                try:
                    # Parse the Excel file first to get expected row count
                    df = self.excel_service.parse_excel_file(file_path)
                    self.excel_service.validate_data(df)
                    acts_data = self.excel_service.transform_dataframe_to_acts(df)
                    expected_count = len(acts_data)
                    
                    logger.info(f"Processing {file_path.name}: Expected {expected_count} records")
                    
                    # Process the import
                    success, message, records_count = self.excel_service.process_import(file_path)
                    
                    if success and expected_count > 0:
                        # Bulk insert (all records are unique)
                        inserted_count = self.acts_repo.bulk_insert(acts_data)
                        
                        # Validate that all rows were processed
                        if inserted_count == expected_count:
                            total_processed += inserted_count
                            logger.info(f"Successfully imported {inserted_count}/{expected_count} records from {file_path.name}")
                            
                            # Archive to processed folder only if all rows imported
                            self.excel_service.archive_file(file_path, success=True)
                        else:
                            # Row count mismatch - treat as failure
                            total_failed += 1
                            error_msg = f"Row count mismatch: Expected {expected_count}, but inserted {inserted_count}"
                            logger.error(f"Failed to import {file_path.name}: {error_msg}")
                            
                            # Archive to failed folder
                            self.excel_service.archive_file(file_path, success=False)
                    else:
                        total_failed += 1
                        logger.error(f"Failed to import {file_path.name}: {message}")
                        
                        # Archive to failed folder
                        self.excel_service.archive_file(file_path, success=False)
                        
                except Exception as e:
                    total_failed += 1
                    logger.error(f"Error importing {file_path.name}: {str(e)}")
                    self.excel_service.archive_file(file_path, success=False)
            
            # Update final status
            final_status = {
                'status': 'completed',
                'message': f'Imported {total_processed} records from {len(excel_files)} file(s)',
                'last_run': job_start.isoformat(),
                'records_processed': total_processed,
                'records_failed': total_failed,
                'files_processed': len(excel_files)
            }
            
            self._update_job_status(final_status)
            logger.info(f"Import job completed: {final_status['message']}")
            
            return final_status
            
        except Exception as e:
            error_msg = f"Import job failed: {str(e)}"
            logger.error(error_msg)
            
            self._update_job_status({
                'status': 'failed',
                'message': error_msg,
                'last_run': job_start.isoformat()
            })
            
            return {'status': 'failed', 'message': error_msg}
    
    def trigger_manual_import(self) -> Dict[str, Any]:
        """
        Trigger an import job manually (on-demand).
        """
        logger.info("Manual import triggered")
        return self.run_import_job()
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current job status from Redis"""
        try:
            status = self.redis_service.get(self.job_status_key)
            if status:
                return status
            else:
                return {
                    'status': 'idle',
                    'message': 'No import jobs have been run yet'
                }
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return {
                'status': 'unknown',
                'message': f'Error retrieving status: {str(e)}'
            }
    
    def _update_job_status(self, status: Dict[str, Any]):
        """Update job status in Redis"""
        try:
            self.redis_service.set(self.job_status_key, status, ttl=86400)  # 24 hour TTL
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")


# Global scheduler instance
_scheduler_instance: Optional[ImportScheduler] = None

def get_scheduler(redis_service: RedisService) -> ImportScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ImportScheduler(redis_service)
    return _scheduler_instance
