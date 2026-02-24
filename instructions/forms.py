from django import forms
from django.db import models

from employees.models import Department, Position

from .models import Instruction


class InstructionForm(forms.ModelForm):
    class Meta:
        model = Instruction
        fields = '__all__'


class InstructionAssignForm(forms.Form):
    class TargetScope(models.TextChoices):
        ALL = 'all', 'Бүх ажилтанд'
        DEPARTMENT = 'department', 'Тодорхой хэлтэст'
        POSITION = 'position', 'Тодорхой албан тушаалд'

    instruction = forms.ModelChoiceField(queryset=Instruction.objects.all().order_by('title'), label='Зааварчилгаа')
    target_scope = forms.ChoiceField(choices=TargetScope.choices, label='Хамрах хүрээ')
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=False,
        label='Хэлтэс',
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.all().order_by('name'),
        required=False,
        label='Албан тушаал',
    )
    completed_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Хийсэн огноо (сонголттой)',
    )

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get('target_scope')
        department = cleaned_data.get('department')
        position = cleaned_data.get('position')

        if scope == self.TargetScope.DEPARTMENT and not department:
            self.add_error('department', 'Хэлтэс сонгоно уу.')

        if scope == self.TargetScope.POSITION and not position:
            self.add_error('position', 'Албан тушаал сонгоно уу.')

        return cleaned_data
