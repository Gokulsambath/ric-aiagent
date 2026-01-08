from app.schema.lead_schema import LeadCreateRequest, LeadResponse
from app.models.lead_model import Lead as LeadModel
from app.repository.base_repo import BaseRepository
from typing import List, Optional

class LeadRepository(BaseRepository[LeadModel]):
    def __init__(self):
        super().__init__(LeadModel)

    def create_lead(self, lead_data: LeadCreateRequest) -> LeadModel:
        """Create a new lead"""
        new_lead = LeadModel(
            company_name=lead_data.company_name,
            contact_person_name=lead_data.contact_person_name,
            email=lead_data.email,
            mobile_number=lead_data.mobile_number,
            session_id=lead_data.session_id,
            thread_id=lead_data.thread_id
        )
        db = self._get_db()
        try:
            db.add(new_lead)
            db.commit()
            db.refresh(new_lead)
            return new_lead
        finally:
            db.close()

    def get_lead_by_id(self, lead_id: int) -> Optional[LeadModel]:
        """Get a lead by ID"""
        db = self._get_db()
        try:
            lead = db.get(LeadModel, lead_id)
            return lead
        finally:
            db.close()

    def get_leads_by_email(self, email: str) -> List[LeadModel]:
        """Get all leads for a specific email"""
        db = self._get_db()
        try:
            leads = db.query(LeadModel).filter(LeadModel.email == email).all()
            return leads
        finally:
            db.close()

    def get_all_leads(self) -> List[LeadModel]:
        """Get all leads"""
        db = self._get_db()
        try:
            leads = db.query(LeadModel).all()
            return leads
        finally:
            db.close()
