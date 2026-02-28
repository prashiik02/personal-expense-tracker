# backend/auth/schemas.py

from pydantic import BaseModel, EmailStr, Field


class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    monthly_income: float = Field(..., gt=0, description="Monthly income in INR (required)")


class LoginSchema(BaseModel):
    email: EmailStr
    password: str