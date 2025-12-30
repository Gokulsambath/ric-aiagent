from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ActsBase(BaseModel):
    """Base schema for Acts matching Excel structure"""
    state: Optional[str] = Field(None, description="State")
    industry: Optional[str] = Field(None, description="Industry sector")
    company_type: Optional[str] = Field(None, description="Company Type and Specific Acts applicable")
    legislative_area: Optional[str] = Field(None, description="Legislative Area")
    central_acts: Optional[str] = Field(None, description="Central Acts & Rules")
    state_acts: Optional[str] = Field(None, description="State Specific Acts & Rules")
    employee_applicability: Optional[str] = Field(None, description="Employee Applicability")

class ActsCreate(ActsBase):
    """Schema for creating new acts"""
    pass

class ActsResponse(ActsBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ActsFilter(BaseModel):
    """Schema for filtering acts"""
    state: Optional[str] = None
    industry: Optional[str] = None
    legislative_area: Optional[str] = None
    employee_applicability: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in company_type, central_acts, and state_acts")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")

class ImportStatusResponse(BaseModel):
    """Schema for import job status"""
    status: str = Field(..., description="Status: idle, running, completed, failed")
    message: Optional[str] = None
    last_run: Optional[datetime] = None
    records_processed: Optional[int] = None
    records_failed: Optional[int] = None
    file_name: Optional[str] = None

class ImportTriggerResponse(BaseModel):
    """Schema for import trigger response"""
    message: str
    job_id: Optional[str] = None
    status: str

