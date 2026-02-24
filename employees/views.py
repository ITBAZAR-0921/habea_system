from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Employee
from .forms import EmployeeForm


@login_required # login hamgaalalt
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, "employees/employee_list.html", {
        "employees": employees
    })

