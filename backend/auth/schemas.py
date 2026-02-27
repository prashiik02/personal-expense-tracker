# backend/auth/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    monthly_income: Optional[float] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str