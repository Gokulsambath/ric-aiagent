from enum import Enum
from pydantic import BaseModel, Field

class OrganisationTypeEnum(str, Enum):
    PRIVATE_LIMITED = "Private Limited Company"
    PUBLIC_LIMITED = "Public Limited Company"
    LLP = "Limited Liability Partnership (LLP)"
    OPC = "One Person Company (OPC)"
    PARTNERSHIP = "Partnership Firm"
    SOLE_PROPRIETORSHIP = "Sole Proprietorship"
    SECTION_8 = "Section 8 Company"
    TRUST = "Trust"
    SOCIETY = "Society"
    UNCLEAR = "Unclear"

class IndustryTypeEnum(str, Enum):
    HEALTHCARE = "Healthcare"
    BFSI = "BFSI"
    EDUCATION = "Education"
    MANUFACTURING = "Manufacturing"
    RETAIL = "Retail"
    IT_SERVICES = "IT Services"
    LOGISTICS = "Logistics"
    ENERGY = "Energy"
    UNCLEAR = "Unclear"

class EmployeeSizeEnum(str, Enum):
    SIZE_1_10 = "1-10"
    SIZE_11_50 = "11-50"
    SIZE_51_200 = "51-200"
    SIZE_201_500 = "201-500"
    SIZE_501_1000 = "501-1000"
    SIZE_1000_PLUS = "1000+"
    UNCLEAR = "Unclear"

from pydantic import BaseModel, Field, AliasChoices

class ClassificationResult(BaseModel):
    organisation_type: OrganisationTypeEnum = Field(..., validation_alias=AliasChoices('organisation_type', 'organization_type'), description="The classified organization type")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score between 0 and 1")

class IndustryClassificationResult(BaseModel):
    industry_type: IndustryTypeEnum = Field(..., description="The classified industry type")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score between 0 and 1")

class EmployeeSizeClassificationResult(BaseModel):
    employee_size: EmployeeSizeEnum = Field(..., description="The classified employee size range")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score between 0 and 1")
