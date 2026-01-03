from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Certification(Base):
    """
    Represents a professional certification obtained by an employee.
    """
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    employee_profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    issuing_organization = Column(String, nullable=False)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    credential_id = Column(String, nullable=True)

    # Relationship
    employee_profile = relationship("EmployeeProfile", back_populates="certifications")
