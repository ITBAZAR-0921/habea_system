from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import InstructionForm, InstructionRecordForm
from .models import Instruction, InstructionRecord


@login_required
def instruction_list(request):
    instructions = Instruction.objects.all().order_by('title')
    due_soon_count = sum(1 for record in InstructionRecord.objects.all() if record.status == InstructionRecord.Status.DUE_SOON)
    overdue_count = sum(1 for record in InstructionRecord.objects.all() if record.status == InstructionRecord.Status.OVERDUE)
    return render(
        request,
        'instructions/instruction_list.html',
        {
            'instructions': instructions,
            'due_soon_count': due_soon_count,
            'overdue_count': overdue_count,
        },
    )


@login_required
def instruction_add(request):
    if request.method == 'POST':
        form = InstructionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('instruction_list')
    else:
        form = InstructionForm()

    return render(request, 'instructions/instruction_form.html', {'form': form})


@login_required
def instruction_record_list(request):
    records = InstructionRecord.objects.select_related('employee', 'instruction').all()
    return render(request, 'instructions/instruction_record_list.html', {'records': records})


@login_required
def instruction_record_add(request):
    if request.method == 'POST':
        form = InstructionRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('instruction_record_list')
    else:
        form = InstructionRecordForm()

    return render(request, 'instructions/instruction_record_form.html', {'form': form})
