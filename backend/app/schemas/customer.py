from uuid import UUID
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    custom_metadata: Optional[dict[str, Any]] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    custom_metadata: Optional[dict[str, Any]] = None


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: Optional[str]
    company_name: Optional[str]
    billing_address: Optional[str]
    tax_id: Optional[str]
    currency: str
    custom_metadata: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)