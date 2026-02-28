from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class LoanParsed(BaseModel):
    principal: Optional[float] = Field(None, description="Principal amount")
    interest_rate: Optional[str] = Field(None, description="Interest rate (may include %)")
    tenure_months: Optional[int] = Field(None, description="Tenure in months")
    emi: Optional[float] = Field(None, description="EMI amount")
    sanction_date: Optional[str] = Field(None, description="Sanction date as string")
    lender: Optional[str] = Field(None, description="Lender name")
    prepayment_clause: Optional[str] = Field(None, description="Any prepayment/foreclosure clause text")
    raw: Optional[Dict[str, Any]] = None


class BudgetSuggestionModel(BaseModel):
    # keys are category names -> suggested monthly budget
    budgets: Dict[str, float]
    explanation: Optional[str]


class AnomalyExplanation(BaseModel):
    likely_cause: Optional[str]
    recommended_steps: Optional[str]
    raw: Optional[Dict[str, Any]] = None
