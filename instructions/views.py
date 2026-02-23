from django.shortcuts import render, redirect
from .models import Instruction
from .forms import InstructionForm


def instruction_list(request):
    instructions = Instruction.objects.all()
    return render(request, 'instructions/instruction_list.html', {
        'instructions': instructions
    })


def instruction_add(request):
    if request.method == "POST":
        form = InstructionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('instruction_list')
    else:
        form = InstructionForm()

    return render(request, 'instructions/instruction_form.html', {
        'form': form
    })
# Create your views here.
