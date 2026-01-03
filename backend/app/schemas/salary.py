from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

# Base schema for common attributes
class SalaryStructureBase(BaseModel):
    basic_salary: Decimal
    hra: Decimal = 0.0
    standard_allowance: Decimal = 0.0
    performance_bonus: Decimal = 0.0
    lta: Decimal = 0.0
    fixed_allowance: Decimal = 0.0
    professional_tax: Decimal = 0.0
    pf_contribution: Decimal = 0.0

# Schema for creating a new salary structure
class SalaryStructureCreate(SalaryStructureBase):
    employee_profile_id: int

# Schema for updating a salary structure
class SalaryStructureUpdate(BaseModel):
    basic_salary: Optional[Decimal] = None
    hra: Optional[Decimal] = None
    standard_allowance: Optional[Decimal] = None
    performance_bonus: Optional[Decimal] = None
    lta: Optional[Decimal] = None
    fixed_allowance: Optional[Decimal] = None
    professional_tax: Optional[Decimal] = None
    pf_contribution: Optional[Decimal] = None

# Schema for salary structure data returned from the API
class SalaryStructure(SalaryStructureBase):
    id: int
    employee_profile_id: int

    class Config:
        from_attributes = True

# Schema for payroll view (including computed salary details)
class SalaryPayroll(SalaryStructure):
    gross_salary: Decimal
    total_deductions: Decimal
    net_salary: Decimal
