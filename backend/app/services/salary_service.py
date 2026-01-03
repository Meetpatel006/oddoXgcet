from decimal import Decimal
from app.models import SalaryStructure

def calculate_net_salary(salary_structure: SalaryStructure) -> dict:
    """
    Calculates the gross and net salary based on the provided salary structure.
    """
    gross_salary = (
        salary_structure.basic_salary +
        salary_structure.hra +
        salary_structure.standard_allowance +
        salary_structure.performance_bonus +
        salary_structure.lta +
        salary_structure.fixed_allowance
    )

    total_deductions = (
        salary_structure.professional_tax +
        salary_structure.pf_contribution
    )

    net_salary = gross_salary - total_deductions

    return {
        "gross_salary": gross_salary,
        "total_deductions": total_deductions,
        "net_salary": net_salary
    }
