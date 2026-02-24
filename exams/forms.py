from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import AttemptResponse, Choice, Exam, Question


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title',
            'description',
            'exam_type',
            'target_type',
            'departments',
            'positions',
            'duration_minutes',
            'pass_score',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'departments': forms.SelectMultiple(attrs={'size': 8}),
            'positions': forms.SelectMultiple(attrs={'size': 8}),
        }

    def clean(self):
        cleaned = super().clean()
        target_type = cleaned.get('target_type')
        departments = cleaned.get('departments')
        positions = cleaned.get('positions')

        if target_type == Exam.TargetType.DEPARTMENT and not departments:
            self.add_error('departments', 'Хэлтэс сонгоно уу.')

        if target_type == Exam.TargetType.POSITION and not positions:
            self.add_error('positions', 'Албан тушаал сонгоно уу.')

        return cleaned


class QuestionWithChoicesForm(forms.ModelForm):
    choice_1 = forms.CharField(label='Сонголт 1', max_length=500)
    choice_2 = forms.CharField(label='Сонголт 2', max_length=500)
    choice_3 = forms.CharField(label='Сонголт 3', max_length=500)
    choice_4 = forms.CharField(label='Сонголт 4', max_length=500)
    correct_choice = forms.ChoiceField(
        label='Зөв хариулт',
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
    )

    class Meta:
        model = Question
        fields = ['text', 'image', 'score', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            choices = list(self.instance.choices.all()[:4])
            for idx in range(4):
                if idx < len(choices):
                    self.fields[f'choice_{idx+1}'].initial = choices[idx].text
                if idx < len(choices) and choices[idx].is_correct:
                    self.fields['correct_choice'].initial = str(idx + 1)

    def clean(self):
        cleaned = super().clean()
        values = [cleaned.get(f'choice_{i}') for i in range(1, 5)]
        values = [v.strip() for v in values if v and v.strip()]

        if len(values) < 2:
            raise forms.ValidationError('Дор хаяж 2 choice оруулна уу.')

        correct = cleaned.get('correct_choice')
        if not correct:
            raise forms.ValidationError('Зөв хариулт сонгоно уу.')

        correct_index = int(correct) - 1
        if correct_index >= len([cleaned.get(f'choice_{i}') for i in range(1, 5)]):
            raise forms.ValidationError('Зөв хариултын индекс буруу байна.')

        return cleaned

    def save(self, commit=True):
        question = super().save(commit=commit)
        if question.pk:
            values = [self.cleaned_data.get(f'choice_{i}', '').strip() for i in range(1, 5)]
            correct_idx = int(self.cleaned_data['correct_choice']) - 1

            existing = list(question.choices.all())
            for i in range(4):
                text = values[i]
                if i < len(existing):
                    choice = existing[i]
                    choice.text = text
                    choice.is_correct = i == correct_idx
                    choice.save()
                else:
                    if text:
                        Choice.objects.create(question=question, text=text, is_correct=i == correct_idx)

            if len(existing) > 4:
                for extra in existing[4:]:
                    extra.delete()

            non_empty = [c for c in question.choices.all() if c.text.strip()]
            if len(non_empty) < 2:
                raise forms.ValidationError('Асуулт бүр дор хаяж 2 choice-той байх ёстой.')
            if sum(1 for c in non_empty if c.is_correct) != 1:
                raise forms.ValidationError('Нэг л зөв хариулттай байх ёстой.')

        return question


class BaseQuestionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        valid_forms = [f for f in self.forms if not f.cleaned_data.get('DELETE', False) and f.cleaned_data]
        if not valid_forms:
            raise forms.ValidationError('Дор хаяж 1 асуулт оруулна уу.')


QuestionFormSet = inlineformset_factory(
    Exam,
    Question,
    form=QuestionWithChoicesForm,
    formset=BaseQuestionFormSet,
    extra=5,
    max_num=30,
    can_delete=True,
)


class QuestionChoiceForm(forms.Form):
    choice = forms.ModelChoiceField(
        queryset=Choice.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
        label='Сонголт',
    )

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super().__init__(*args, **kwargs)
        self.question = question
        self.fields['choice'].queryset = question.choices.all()

    def save_official(self, attempt):
        return AttemptResponse.objects.update_or_create(
            attempt=attempt,
            question=self.question,
            defaults={'selected_choice': self.cleaned_data['choice']},
        )
