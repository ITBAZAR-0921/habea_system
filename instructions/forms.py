from django import forms
from .models import Instruction


class InstructionForm(forms.ModelForm):
    class Meta:
        model = Instruction
        fields = '__all__'