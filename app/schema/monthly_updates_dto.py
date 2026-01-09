from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date

class MonthlyUpdateBase(BaseModel):
    """Base schema for Monthly Updates matching Excel structure"""
    title: str = Field(..., description="Update title")
    category: str = Field(..., description="Category (Labour, Taxation, EHS, etc.)")
    description: str = Field(..., description="Detailed description of the update")
    change_type: str = Field(..., description="Type of change (Circular, Notification, etc.)")
    state: str = Field(..., description="State name or Central")
    effective_date: date = Field(..., description="Date when the update becomes effective")
    update_date: date = Field(..., description="Date when the update was published")
    source_link: Optional[str] = Field(None, description="Link to source document")

class MonthlyUpdateCreate(MonthlyUpdateBase):
    """Schema for creating new monthly updates"""
    pass

class MonthlyUpdateResponse(MonthlyUpdateBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MonthlyUpdateFilter(BaseModel):
    """Schema for filtering monthly updates"""
    category: Optional[str] = Field(None, description="Filter by category")
    state: Optional[str] = Field(None, description="Filter by state")
    change_type: Optional[str] = Field(None, description="Filter by change type")
    from_date: Optional[date] = Field(None, description="Filter updates from this effective date")
    to_date: Optional[date] = Field(None, description="Filter updates to this effective date")
    search: Optional[str] = Field(None, description="Search in title and description")
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
    records_processed: Optional[int] = 0
