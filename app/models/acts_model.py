from sqlalchemy import String, Column, Text, Index, UniqueConstraint
from app.models.base_model import BaseModel

class Acts(BaseModel):
    __tablename__ = "acts"

    # Columns matching Excel structure (id, created_at, updated_at inherited from BaseModel)
    state = Column(Text, nullable=True, index=True)
    industry = Column(Text, nullable=True, index=True)
    company_type = Column(Text, nullable=True)  # "Company Type and Specific Acts applicable for Each type of Company"
    legislative_area = Column(Text, nullable=True, index=True)  # "Legislative Area"
    central_acts = Column(Text, nullable=True)  # "Central Acts & Rules"
    state_acts = Column(Text, nullable=True)  # "State Specific Acts & Rules"
    employee_applicability = Column(Text, nullable=True, index=True)  # "Employee Applicability"
    
    # Composite indexes for common filter combinations
    __table_args__ = (
        Index('idx_state_industry', 'state', 'industry'),
        Index('idx_state_legislative_area', 'state', 'legislative_area'),
        Index('idx_industry_legislative_area', 'industry', 'legislative_area'),
        Index('idx_state_industry_legislative', 'state', 'industry', 'legislative_area'),
    )

