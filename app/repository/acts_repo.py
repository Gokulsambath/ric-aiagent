from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.dialects.postgresql import insert
from app.models.acts_model import Acts as ActsModel
from app.repository.base_repo import BaseRepository
from app.schema.acts_dto import ActsFilter

class Acts(BaseRepository[ActsModel]):
    def __init__(self):
        super().__init__(ActsModel)

    def bulk_upsert(self, acts_data: List[Dict[str, Any]]) -> int:
        """
        Bulk insert or update acts data.
        Uses PostgreSQL's ON CONFLICT for upsert functionality.
        Returns the number of records processed.
        """
        db = self._get_db()
        try:
            if not acts_data:
                return 0
            
            # For PostgreSQL, use insert with on_conflict_do_update
            stmt = insert(ActsModel).values(acts_data)
            
            # Update all fields except id and created_at on conflict
            update_dict = {
                c.name: c 
                for c in stmt.excluded 
                if c.name not in ['id', 'created_at']
            }
            
            stmt = stmt.on_conflict_do_update(
                constraint='uq_state_industry_legislative',  # Using the unique constraint name
                set_=update_dict
            )
            
            result = db.execute(stmt)
            db.commit()
            return len(acts_data)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def bulk_insert(self, acts_data: List[Dict[str, Any]]) -> int:
        """
        Simple bulk insert without upsert logic.
        Useful for fresh imports after truncate.
        """
        db = self._get_db()
        try:
            if not acts_data:
                return 0
            
            db.bulk_insert_mappings(ActsModel, acts_data)
            db.commit()
            return len(acts_data)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def find_by_filters(self, filters: ActsFilter) -> tuple[List[ActsModel], int]:
        """
        Find acts by various filters with pagination.
        Returns tuple of (results, total_count)
        """
        db = self._get_db()
        try:
            query = db.query(ActsModel)
            
            # Apply filters
            if filters.state:
                query = query.filter(ActsModel.state == filters.state)
            
            if filters.industry:
                query = query.filter(ActsModel.industry == filters.industry)
            
            if filters.legislative_area:
                query = query.filter(ActsModel.legislative_area == filters.legislative_area)
            
            if filters.employee_applicability:
                query = query.filter(ActsModel.employee_applicability == filters.employee_applicability)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        ActsModel.company_type.ilike(search_term),
                        ActsModel.central_acts.ilike(search_term),
                        ActsModel.state_acts.ilike(search_term)
                    )
                )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            query = query.offset(filters.skip).limit(filters.limit)
            
            results = query.all()
            return results, total_count
        finally:
            db.close()

    def find_by_id(self, act_id: int) -> Optional[ActsModel]:
        """Find a specific act by ID"""
        db = self._get_db()
        try:
            return db.get(ActsModel, act_id)
        finally:
            db.close()

    def truncate_table(self) -> None:
        """Clear all acts from the table"""
        db = self._get_db()
        try:
            db.query(ActsModel).delete()
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
            column = getattr(ActsModel, column_name)
            results = db.query(column).distinct().filter(column.isnot(None)).all()
            return [r[0] for r in results]
        finally:
            db.close()
