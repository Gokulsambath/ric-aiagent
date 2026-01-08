from fastapi import APIRouter, HTTPException, status
from app.schema.lead_schema import LeadCreateRequest, LeadResponse
from app.repository.lead_repo import LeadRepository
from typing import List

lead_router = APIRouter(prefix="/api/leads", tags=["leads"])

@lead_router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(lead_data: LeadCreateRequest):
    """
    Create a new lead from the lead generation form
    """
    try:
        repo = LeadRepository()
        new_lead = repo.create_lead(lead_data)
        return new_lead
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )

@lead_router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int):
    """
    Get a specific lead by ID
    """
    repo = LeadRepository()
    lead = repo.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead

@lead_router.get("/email/{email}", response_model=List[LeadResponse])
async def get_leads_by_email(email: str):
    """
    Get all leads for a specific email address
    """
    repo = LeadRepository()
    leads = repo.get_leads_by_email(email)
    return leads

@lead_router.get("/", response_model=List[LeadResponse])
async def get_all_leads():
    """
    Get all leads
    """
    repo = LeadRepository()
    leads = repo.get_all_leads()
    return leads
