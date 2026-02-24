from django import forms

from .models import Instruction, InstructionRecord


class InstructionForm(forms.ModelForm):
    class Meta:
        model = Instruction
        fields = '__all__'


class InstructionRecordForm(forms.ModelForm):
    class Meta:
        model = InstructionRecord
        fields = ['employee', 'instruction', 'completed_on', 'valid_until', 'trainer_name', 'notes']
        widgets = {
            'completed_on': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
