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
                query = query.filter(
                    or_(
                        ActsModel.state == filters.state,
                        ActsModel.state.ilike("all"),
                        ActsModel.state.ilike("central")
                    )
                )
            
            if filters.industry:
                query = query.filter(
                    or_(
                        ActsModel.industry == filters.industry,
                        ActsModel.industry.ilike("all")
                    )
                )
            
            if filters.legislative_area:
                query = query.filter(
                    or_(
                        ActsModel.legislative_area == filters.legislative_area,
                        ActsModel.legislative_area.ilike("all")
                    )
                )
            
            if filters.employee_applicability:
                query = query.filter(
                     or_(
                        ActsModel.employee_applicability == filters.employee_applicability,
                        ActsModel.employee_applicability.ilike("all")
                     )
                )
            
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

    def find_by_botpress_variables(
        self, 
        state: Optional[str] = None,
        industry: Optional[str] = None,
        employee_size: Optional[str] = None,
        company_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find acts based on Botpress user session variables.
        Returns serialized dict representation for JSON streaming.
        
        Args:
            state: State name from Botpress user.state
            industry: Industry from Botpress user.industry
            employee_size: Employee size from Botpress user.size
            limit: Maximum number of results to return
            
        Returns:
            List of acts as dictionaries
        """
        db = self._get_db()
        try:
            query = db.query(ActsModel)
            
            # Apply filters based on available Botpress variables
            if state:
                query = query.filter(
                    or_(
                        ActsModel.state == state,
                        ActsModel.state.ilike("all"),
                        ActsModel.state.ilike("central")
                    )

                )
            
            if industry:
                query = query.filter(
                    or_(
                        ActsModel.industry == industry,
                        ActsModel.industry.ilike("all")
                    )
                )

            if company_type:
                query = query.filter(
                    or_(
                        ActsModel.company_type == company_type,
                        ActsModel.company_type.ilike("all")
                    )
                )
                
            if employee_size:
                # Match either the specific size OR "Applies to all"
                query = query.filter(
                    or_(
                        ActsModel.employee_applicability == employee_size,
                        ActsModel.employee_applicability.ilike("all")
                    )
                )
            
            # Limit results
            query = query.limit(limit)
            
            results = query.all()
            
            # Convert to dict for JSON serialization
            return [
                {
                    'id': act.id,
                    'state': act.state,
                    'industry': act.industry,
                    'company_type': act.company_type,
                    'legislative_area': act.legislative_area,
                    'central_acts': act.central_acts,
                    'state_acts': act.state_acts,
                    'employee_applicability': act.employee_applicability,
                }
                for act in results
            ]
        finally:
            db.close()
