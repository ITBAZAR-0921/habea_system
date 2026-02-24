from config.permissions import role_required
from django.shortcuts import render

from .models import Employee


@role_required(['system_admin', 'hse_manager', 'department_head'])
def employee_list(request):
    employees = (
        Employee.objects.select_related('department', 'position', 'location')
        .all()
        .order_by('last_name', 'first_name')
    )
    return render(request, 'employees/employee_list.html', {'employees': employees})
