from django import forms
from django.forms import inlineformset_factory

from .models import Training, TrainingMaterial, TrainingParticipation


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = [
            'title',
            'description',
            'training_type',
            'departments',
            'positions',
            'employees',
            'start_date',
            'end_date',
            'trainer_name',
            'required',
            'is_active',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Сургалтын гарчиг'}),
            'description': forms.Textarea(
                attrs={
                    'rows': 5,
                    'class': 'form-control',
                    'style': 'height: 120px; resize: vertical;',
                    'placeholder': 'Сургалтын тайлбар',
                }
            ),
            'training_type': forms.Select(attrs={'class': 'form-select'}),
            'departments': forms.SelectMultiple(attrs={'class': 'form-select select2-multi'}),
            'positions': forms.SelectMultiple(attrs={'class': 'form-select select2-multi'}),
            'employees': forms.SelectMultiple(attrs={'class': 'form-select select2-multi'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'trainer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Сургагчийн нэр'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        training_type = cleaned.get('training_type')

        if training_type == Training.TrainingType.DEPARTMENT and not cleaned.get('departments'):
            self.add_error('departments', 'Хэлтэс сонгоно уу.')
        if training_type == Training.TrainingType.POSITION and not cleaned.get('positions'):
            self.add_error('positions', 'Албан тушаал сонгоно уу.')
        if training_type == Training.TrainingType.SPECIFIC_EMPLOYEE and not cleaned.get('employees'):
            self.add_error('employees', 'Ажилтан сонгоно уу.')

        return cleaned


class TrainingMaterialForm(forms.ModelForm):
    class Meta:
        model = TrainingMaterial
        fields = ['title', 'material_type', 'file', 'text_content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Материалын нэр'}),
            'material_type': forms.Select(attrs={'class': 'form-select material-type-field'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control material-file-field'}),
            'text_content': forms.Textarea(
                attrs={
                    'rows': 8,
                    'class': 'form-control material-text-field material-text-rich',
                    'placeholder': 'Text агуулга оруулна уу',
                }
            ),
        }

    def clean(self):
        cleaned = super().clean()
        material_type = cleaned.get('material_type')
        file_obj = cleaned.get('file')
        text_content = (cleaned.get('text_content') or '').strip()

        if material_type in {TrainingMaterial.MaterialType.IMAGE, TrainingMaterial.MaterialType.PDF}:
            if not file_obj and not self.instance.file:
                self.add_error('file', 'Image/PDF материалд файл заавал оруулна.')
            if text_content:
                self.add_error('text_content', 'Image/PDF материалд text_content хоосон байна.')

        if material_type == TrainingMaterial.MaterialType.TEXT:
            if not text_content:
                self.add_error('text_content', 'Text материалд агуулга заавал оруулна.')
            if file_obj:
                self.add_error('file', 'Text материалд файл оруулахгүй.')

        return cleaned


class ParticipationStatusForm(forms.ModelForm):
    class Meta:
        model = TrainingParticipation
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            (TrainingParticipation.Status.ATTENDED, 'Суусан'),
            (TrainingParticipation.Status.COMPLETED, 'Дууссан'),
        ]


TrainingMaterialFormSet = inlineformset_factory(
    Training,
    TrainingMaterial,
    form=TrainingMaterialForm,
    extra=1,
    can_delete=True,
)
