from django import forms

from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = [
            'title',
            'content',
            'notice_type',
            'departments',
            'positions',
            'employees',
            'requires_acknowledgement',
            'is_active',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'departments': forms.SelectMultiple(attrs={'size': 8}),
            'positions': forms.SelectMultiple(attrs={'size': 8}),
            'employees': forms.SelectMultiple(attrs={'size': 8}),
        }

    def clean(self):
        cleaned_data = super().clean()
        notice_type = cleaned_data.get('notice_type')
        departments = cleaned_data.get('departments')
        positions = cleaned_data.get('positions')
        employees = cleaned_data.get('employees')

        if notice_type == Notice.NoticeType.DEPARTMENT and not departments:
            self.add_error('departments', 'Хэлтэс сонгоно уу.')

        if notice_type == Notice.NoticeType.POSITION and not positions:
            self.add_error('positions', 'Албан тушаал сонгоно уу.')

        if notice_type == Notice.NoticeType.SPECIFIC_EMPLOYEE and not employees:
            self.add_error('employees', 'Ажилтан сонгоно уу.')

        return cleaned_data
