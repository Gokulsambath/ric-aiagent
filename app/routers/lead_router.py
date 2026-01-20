from fastapi import APIRouter, HTTPException, status
from app.schema.lead_schema import LeadCreateRequest, LeadResponse
from app.repository.lead_repo import LeadRepository
from typing import List
from pydantic import EmailStr
from app.configs.settings import settings

lead_router = APIRouter(prefix="/api/leads", tags=["leads"])

@lead_router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(lead_data: LeadCreateRequest):
    """
    Create a new lead from the lead generation form
    """
    print("\n" + "="*80, flush=True)
    print("🟢 LEAD SUBMISSION STARTED", flush=True)
    print("="*80, flush=True)
    
    try:
        # Log received data
        print(f"📥 Received lead data:", flush=True)
        print(f"   - Company: {lead_data.company_name}", flush=True)
        print(f"   - Contact Person: {lead_data.contact_person_name}", flush=True)
        print(f"   - Email: {lead_data.email}", flush=True)
        print(f"   - Mobile: {lead_data.mobile_number}", flush=True)
        print(f"   - Session ID: {lead_data.session_id}", flush=True)
        
        # Save to database
        print("\n💾 Saving lead to database...", flush=True)
        repo = LeadRepository()
        new_lead = repo.create_lead(lead_data)
        print(f"✅ Lead saved successfully with ID: {new_lead.id}", flush=True)
        
        # Send email notification
        print("\n📧 Starting email notification process...", flush=True)
        try:
            from app.repository.email_repo import Email as EmailRepo
            from app.schema.email_dto import Email as EmailDTO

            print("   ✓ Email modules imported", flush=True)
            
            email_repo = EmailRepo()
            print("   ✓ Email repository initialized", flush=True)
            
            email_content = f"""
            <h3>New Lead Captured!</h3>
            <p><b>Company Name:</b> {new_lead.company_name}</p>
            <p><b>Contact Person:</b> {new_lead.contact_person_name}</p>
            <p><b>Email:</b> {new_lead.email}</p>
            <p><b>Mobile Number:</b> {new_lead.mobile_number}</p>
            <p><b>Session ID:</b> {new_lead.session_id}</p>
            """
            print("   ✓ Email content prepared", flush=True)
            
            print(f"\n📤 Creating email DTO:", flush=True)
            print(f"   - To: {settings.mail.mail_to}", flush=True)
            print(f"   - Subject: New Lead: {new_lead.company_name}", flush=True)
            print(f"   - Customer Email: {new_lead.email}", flush=True)
            
            try:
                email_data = EmailDTO(
                    email=[settings.mail.mail_to],
                    subject=f"New Lead: {new_lead.company_name}",
                    message=email_content,
                    name="RIC Agent",
                    customer_email=new_lead.email
                )
                print("   ✅ EmailDTO created and validated successfully", flush=True)
                
                print("\n🚀 Sending email in background...", flush=True)
                result = email_repo.sendEmailBackground(email_data)
                print(f"   ✅ Email queued: {result}", flush=True)
                print(f"\n✅ SUCCESS: Notification email sent to {settings.mail.mail_to}", flush=True)
                
            except Exception as ve:
                print(f"\n❌ ERROR: EmailDTO Validation or Send Failed:", flush=True)
                print(f"   Error Type: {type(ve).__name__}", flush=True)
                print(f"   Error Message: {str(ve)}", flush=True)
                import traceback
                print(f"   Traceback:\n{traceback.format_exc()}", flush=True)
                
        except Exception as e:
            print(f"\n❌ ERROR: Failed to send lead notification email:", flush=True)
            print(f"   Error Type: {type(e).__name__}", flush=True)
            print(f"   Error Message: {str(e)}", flush=True)
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}", flush=True)

        print("\n" + "="*80, flush=True)
        print("🟢 LEAD SUBMISSION COMPLETED SUCCESSFULLY", flush=True)
        print("="*80 + "\n", flush=True)
        
        return new_lead
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: Lead creation failed:", flush=True)
        print(f"   Error Type: {type(e).__name__}", flush=True)
        print(f"   Error Message: {str(e)}", flush=True)
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}", flush=True)
        print("="*80 + "\n", flush=True)
        
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

@lead_router.get("", response_model=List[LeadResponse])
async def get_all_leads():
    """
    Get all leads
    """
    repo = LeadRepository()
    leads = repo.get_all_leads()
    return leads
