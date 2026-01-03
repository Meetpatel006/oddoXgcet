from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SalaryStructure(Base):
    """
    Represents the salary structure for an employee.
    It includes various components of the salary package.
    """
    __tablename__ = "salary_structures"

    id = Column(Integer, primary_key=True, index=True)
    employee_profile_id = Column(Integer, ForeignKey("employee_profiles.id"), unique=True, nullable=False)
    
    basic_salary = Column(Numeric(10, 2), nullable=False)
    hra = Column(Numeric(10, 2), default=0.0)
    standard_allowance = Column(Numeric(10, 2), default=0.0)
    performance_bonus = Column(Numeric(10, 2), default=0.0)
    lta = Column(Numeric(10, 2), default=0.0) # Leave Travel Allowance
    fixed_allowance = Column(Numeric(10, 2), default=0.0)
    
    professional_tax = Column(Numeric(10, 2), default=0.0)
    pf_contribution = Column(Numeric(10, 2), default=0.0)

    # Relationship
    employee_profile = relationship("EmployeeProfile", back_populates="salary_structure")
