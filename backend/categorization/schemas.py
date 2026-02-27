from __future__ import annotations

from datetime import date
from typing import List, Optional, Literal, Any

from pydantic import BaseModel, Field


class LineItemSchema(BaseModel):
    name: str = Field(min_length=1)
    amount: float


class RawTransactionSchema(BaseModel):
    transaction_id: Optional[str] = None
    date: str
    description: str = Field(min_length=1)
    amount: float
    currency: str = "INR"
    line_items: Optional[List[LineItemSchema]] = None


class CategorizeBatchSchema(BaseModel):
    transactions: Optional[List[RawTransactionSchema]] = None
    csv_text: Optional[str] = None
    include_summary: bool = True
    return_results: bool = True


class CategorizeSmsSchema(BaseModel):
    sms_text: str = Field(min_length=1)
    bank: Literal["hdfc", "sbi"]


class CategorizeCorrectionSchema(BaseModel):
    transaction_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    merchant_name: Optional[str] = None
    old_category: str = Field(min_length=1)
    new_category: str = Field(min_length=1)
    new_subcategory: str = Field(min_length=1)

