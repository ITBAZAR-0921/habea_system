from django.shortcuts import render, redirect
from .models import Employee
from .forms import EmployeeForm
# Create your views here.
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, "employees/employee_list.html", {
        "employees": employees
    })

def employee_add(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/employee_list/')
    else:
        form = EmployeeForm()

    return render(request, 'employees/employee_form.html', {
        'form': form
    })