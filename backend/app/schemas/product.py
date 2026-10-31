from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(default=None, max_length=100)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    sku: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)