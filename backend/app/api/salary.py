from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, EmployeeProfile, SalaryStructure, UserRole
from app.schemas import SalaryStructure as SalaryStructureSchema, SalaryStructureCreate, SalaryStructureUpdate, SalaryPayroll
from app.auth.dependencies import get_current_active_user, get_current_active_user_with_roles
from app.services.salary_service import calculate_net_salary

router = APIRouter()

@router.post("/structure", response_model=SalaryStructureSchema, status_code=status.HTTP_201_CREATED)
def create_salary_structure(
    salary_structure_in: SalaryStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Create a new salary structure for an employee. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == salary_structure_in.employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    existing_structure = db.query(SalaryStructure).filter(SalaryStructure.employee_profile_id == salary_structure_in.employee_profile_id).first()
    if existing_structure:
        raise HTTPException(status_code=400, detail="Salary structure already exists for this employee. Use PUT to update.")

    db_salary_structure = SalaryStructure(**salary_structure_in.model_dump())
    db.add(db_salary_structure)
    db.commit()
    db.refresh(db_salary_structure)
    return db_salary_structure

@router.put("/structure/{salary_structure_id}", response_model=SalaryStructureSchema)
def update_salary_structure(
    salary_structure_id: int,
    salary_structure_in: SalaryStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Update an existing salary structure. (Admin or HR Officer only)
    """
    db_salary_structure = db.query(SalaryStructure).filter(SalaryStructure.id == salary_structure_id).first()
    if not db_salary_structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")

    update_data = salary_structure_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_salary_structure, field, value)
    
    db.add(db_salary_structure)
    db.commit()
    db.refresh(db_salary_structure)
    return db_salary_structure

@router.get("/me", response_model=SalaryStructureSchema)
def get_my_salary_structure(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current employee's salary structure.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")
    
    salary_structure = db.query(SalaryStructure).filter(SalaryStructure.employee_profile_id == employee_profile.id).first()
    if not salary_structure:
        raise HTTPException(status_code=404, detail="Salary structure not found for this employee")
    
    return salary_structure

@router.get("/all", response_model=List[SalaryPayroll])
def get_all_payroll_data(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Retrieve all payroll data with computed gross and net salaries. (Admin or HR Officer only)
    """
    salary_structures = db.query(SalaryStructure).offset(skip).limit(limit).all()
    
    payroll_data = []
    for ss in salary_structures:
        calculated_salary = calculate_net_salary(ss)
        payroll_entry = SalaryPayroll(
            id=ss.id,
            employee_profile_id=ss.employee_profile_id,
            basic_salary=ss.basic_salary,
            hra=ss.hra,
            standard_allowance=ss.standard_allowance,
            performance_bonus=ss.performance_bonus,
            lta=ss.lta,
            fixed_allowance=ss.fixed_allowance,
            professional_tax=ss.professional_tax,
            pf_contribution=ss.pf_contribution,
            gross_salary=calculated_salary["gross_salary"],
            total_deductions=calculated_salary["total_deductions"],
            net_salary=calculated_salary["net_salary"],
        )
        payroll_data.append(payroll_entry)
        
    return payroll_data

@router.get("/{employee_profile_id}/slip", response_model=SalaryPayroll)
def get_salary_slip_data(
    employee_profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Retrieve salary slip data for a specific employee. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
        
    salary_structure = db.query(SalaryStructure).filter(SalaryStructure.employee_profile_id == employee_profile_id).first()
    if not salary_structure:
        raise HTTPException(status_code=404, detail="Salary structure not found for this employee")
        
    calculated_salary = calculate_net_salary(salary_structure)
    
    payroll_entry = SalaryPayroll(
        id=salary_structure.id,
        employee_profile_id=salary_structure.employee_profile_id,
        basic_salary=salary_structure.basic_salary,
        hra=salary_structure.hra,
        standard_allowance=salary_structure.standard_allowance,
        performance_bonus=salary_structure.performance_bonus,
        lta=salary_structure.lta,
        fixed_allowance=salary_structure.fixed_allowance,
        professional_tax=salary_structure.professional_tax,
        pf_contribution=salary_structure.pf_contribution,
        gross_salary=calculated_salary["gross_salary"],
        total_deductions=calculated_salary["total_deductions"],
        net_salary=calculated_salary["net_salary"],
    )
    
    return payroll_entry
