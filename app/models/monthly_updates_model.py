from sqlalchemy import String, Column, Text, Date, Index
from app.models.base_model import BaseModel

class MonthlyUpdates(BaseModel):
    __tablename__ = "monthly_updates"

    # Columns matching Excel structure (id, created_at, updated_at inherited from BaseModel)
    title = Column(Text, nullable=False, index=True)  # "Title"
    category = Column(Text, nullable=False, index=True)  # "Category ID" (Labour, Taxation, EHS, etc.)
    description = Column(Text, nullable=False)  # "Description"
    change_type = Column(Text, nullable=False, index=True)  # "Change Type" (Circular, Notification, etc.)
    state = Column(Text, nullable=False, index=True)  # "State" (Central, state names)
    effective_date = Column(Date, nullable=False, index=True)  # "Effective Date"
    update_date = Column(Date, nullable=False, index=True)  # "Update Date"
    source_link = Column(Text, nullable=True)  # "Source Link" (URL to source document)
    
    # Composite indexes for common filter combinations
    __table_args__ = (
        Index('idx_category_state', 'category', 'state'),
        Index('idx_category_change_type', 'category', 'change_type'),
        Index('idx_state_change_type', 'state', 'change_type'),
        Index('idx_effective_date', 'effective_date'),
        Index('idx_update_date', 'update_date'),
        Index('idx_category_effective_date', 'category', 'effective_date'),
    )
