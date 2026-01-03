from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class BankDetail(Base):
    """
    Represents the bank details of an employee.
    This information is used for payroll processing.
    """
    __tablename__ = "bank_details"

    id = Column(Integer, primary_key=True, index=True)
    employee_profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    account_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    ifsc_code = Column(String, nullable=False)
    branch_name = Column(String, nullable=False)

    # Relationship
    employee_profile = relationship("EmployeeProfile", back_populates="bank_details")
