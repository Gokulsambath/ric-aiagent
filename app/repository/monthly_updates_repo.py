from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.dialects.postgresql import insert
from app.models.monthly_updates_model import MonthlyUpdates as MonthlyUpdatesModel
from app.repository.base_repo import BaseRepository
from app.schema.monthly_updates_dto import MonthlyUpdateFilter

class MonthlyUpdates(BaseRepository[MonthlyUpdatesModel]):
    def __init__(self):
        super().__init__(MonthlyUpdatesModel)

    def bulk_upsert(self, updates_data: List[Dict[str, Any]]) -> int:
        """
        Bulk insert or update monthly updates data.
        Uses PostgreSQL's ON CONFLICT for upsert functionality.
        Returns the number of records processed.
        """
        db = self._get_db()
        try:
            if not updates_data:
                return 0
            
            # For PostgreSQL, use insert with on_conflict_do_update
            stmt = insert(MonthlyUpdatesModel).values(updates_data)
            
            # Update all fields except id and created_at on conflict
            # We'll use a composite key of title, state, and effective_date for conflict detection
            update_dict = {
                c.name: c 
                for c in stmt.excluded 
                if c.name not in ['id', 'created_at']
            }
            
            # Note: This assumes we'll add a unique constraint in the migration
            # For now, we'll just do simple insert (can be changed to upsert later)
            stmt = stmt.on_conflict_do_nothing()
            
            result = db.execute(stmt)
            db.commit()
            return len(updates_data)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def bulk_insert(self, updates_data: List[Dict[str, Any]]) -> int:
        """
        Simple bulk insert without upsert logic.
        Useful for fresh imports after truncate.
        """
        db = self._get_db()
        try:
            if not updates_data:
                return 0
            
            db.bulk_insert_mappings(MonthlyUpdatesModel, updates_data)
            db.commit()
            return len(updates_data)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def find_by_filters(self, filters: MonthlyUpdateFilter) -> tuple[List[MonthlyUpdatesModel], int]:
        """
        Find monthly updates by various filters with pagination.
        Returns tuple of (results, total_count)
        """
        db = self._get_db()
        try:
            query = db.query(MonthlyUpdatesModel)
            
            # Apply filters
            if filters.category:
                query = query.filter(MonthlyUpdatesModel.category == filters.category)
            
            if filters.state:
                query = query.filter(MonthlyUpdatesModel.state == filters.state)
            
            if filters.change_type:
                query = query.filter(MonthlyUpdatesModel.change_type == filters.change_type)
            
            if filters.from_date:
                query = query.filter(MonthlyUpdatesModel.effective_date >= filters.from_date)
            
            if filters.to_date:
                query = query.filter(MonthlyUpdatesModel.effective_date <= filters.to_date)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        MonthlyUpdatesModel.title.ilike(search_term),
                        MonthlyUpdatesModel.description.ilike(search_term)
                    )
                )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination and ordering (most recent first)
            query = query.order_by(MonthlyUpdatesModel.effective_date.desc())
            query = query.offset(filters.skip).limit(filters.limit)
            
            results = query.all()
            return results, total_count
        finally:
            db.close()

    def find_by_id(self, update_id: int) -> Optional[MonthlyUpdatesModel]:
        """Find a specific monthly update by ID"""
        db = self._get_db()
        try:
            return db.get(MonthlyUpdatesModel, update_id)
        finally:
            db.close()

    def truncate_table(self) -> None:
        """Clear all monthly updates from the table"""
        db = self._get_db()
        try:
            db.query(MonthlyUpdatesModel).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_distinct_values(self, column_name: str) -> List[str]:
        """Get distinct values for a column (useful for filters)"""
        db = self._get_db()
        try:
            column = getattr(MonthlyUpdatesModel, column_name)
            results = db.query(column).distinct().filter(column.isnot(None)).order_by(column).all()
            return [r[0] for r in results]
        finally:
            db.close()

    def find_recent_updates(self, days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find recent updates from the last N days.
        Returns serialized dict representation for JSON streaming.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results to return
            
        Returns:
            List of updates as dictionaries
        """
        db = self._get_db()
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now().date() - timedelta(days=days)
            
            query = db.query(MonthlyUpdatesModel)
            query = query.filter(MonthlyUpdatesModel.update_date >= cutoff_date)
            query = query.order_by(MonthlyUpdatesModel.update_date.desc())
            query = query.limit(limit)
            
            results = query.all()
            
            # Convert to dict for JSON serialization
            return [
                {
                    'id': update.id,
                    'title': update.title,
                    'category': update.category,
                    'description': update.description,
                    'change_type': update.change_type,
                    'state': update.state,
                    'effective_date': update.effective_date.isoformat() if update.effective_date else None,
                    'update_date': update.update_date.isoformat() if update.update_date else None,
                    'source_link': update.source_link,
                }
                for update in results
            ]
        finally:
            db.close()
