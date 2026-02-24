from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.permissions import role_required
from employees.models import Employee

from .forms import InstructionAssignForm, InstructionForm
from .models import Instruction, InstructionRecord


MANAGER_ROLES = ['system_admin', 'hse_manager', 'department_head']


def _build_employee_queryset(scope, department=None, position=None):
    queryset = Employee.objects.select_related('department', 'position', 'user').all()
    if scope == InstructionAssignForm.TargetScope.DEPARTMENT:
        return queryset.filter(department=department)
    if scope == InstructionAssignForm.TargetScope.POSITION:
        return queryset.filter(position=position)
    return queryset


@role_required(MANAGER_ROLES)
def instruction_list(request):
    instructions = Instruction.objects.all().order_by('title')
    return render(request, 'instructions/instruction_list.html', {'instructions': instructions})


@role_required(MANAGER_ROLES)
def instruction_add(request):
    if request.method == 'POST':
        form = InstructionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Зааварчилгаа амжилттай нэмэгдлээ.')
            return redirect('instruction_list')
    else:
        form = InstructionForm()

    return render(request, 'instructions/instruction_form.html', {'form': form})


@role_required(MANAGER_ROLES)
def instruction_record_list(request):
    records = InstructionRecord.objects.select_related('employee', 'instruction').all()
    return render(request, 'instructions/instruction_record_list.html', {'records': records})


@role_required(MANAGER_ROLES)
def instruction_record_add(request):
    form = InstructionAssignForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        instruction = form.cleaned_data['instruction']
        target_scope = form.cleaned_data['target_scope']
        department = form.cleaned_data['department']
        position = form.cleaned_data['position']
        completed_date = form.cleaned_data['completed_date']

        employees = _build_employee_queryset(target_scope, department, position)

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for employee in employees:
                _, created = InstructionRecord.objects.update_or_create(
                    employee=employee,
                    instruction=instruction,
                    defaults={
                        'completed_date': completed_date,
                        'acknowledged': False,
                        'acknowledged_date': None,
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        messages.success(
            request,
            f'Зааварчилгаа өгөгдлөө: шинэ {created_count}, шинэчлэгдсэн {updated_count}.',
        )
        return redirect('instruction_record_list')

    return render(request, 'instructions/instruction_record_form.html', {'form': form})


@role_required(['employee'])
def my_instruction_records(request):
    employee = get_object_or_404(Employee, user=request.user)
    records = InstructionRecord.objects.select_related('instruction').filter(employee=employee)
    return render(request, 'instructions/my_instruction_records.html', {'records': records})


@role_required(['employee'])
def acknowledge_instruction(request, record_id):
    if request.method != 'POST':
        return redirect('my_instruction_records')

    employee = get_object_or_404(Employee, user=request.user)
    record = get_object_or_404(InstructionRecord, pk=record_id, employee=employee)
    if not record.acknowledged:
        record.acknowledged = True
        record.acknowledged_date = timezone.localdate()
        record.save(update_fields=['acknowledged', 'acknowledged_date', 'next_due_date'])
        messages.success(request, 'Зааварчилгаатай танилцсан тэмдэглэл амжилттай хадгалагдлаа.')

    return redirect('my_instruction_records')
