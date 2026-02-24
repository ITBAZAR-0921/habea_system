from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Department, Employee, Position


class Exam(models.Model):
    class ExamType(models.TextChoices):
        OFFICIAL = 'official', 'Албан ёсны'
        PRACTICE = 'practice', 'Жишиг'

    class TargetType(models.TextChoices):
        ORGANIZATION_WIDE = 'organization_wide', 'Бүх ажилтан'
        DEPARTMENT = 'department', 'Хэлтсийн'
        POSITION = 'position', 'Албан тушаалын'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    exam_type = models.CharField(max_length=16, choices=ExamType.choices, default=ExamType.OFFICIAL)
    target_type = models.CharField(max_length=32, choices=TargetType.choices, default=TargetType.ORGANIZATION_WIDE)

    departments = models.ManyToManyField(Department, blank=True, related_name='exams')
    positions = models.ManyToManyField(Position, blank=True, related_name='exams')

    duration_minutes = models.PositiveIntegerField(default=30)
    pass_score = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_exams')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def clean(self):
        if self.target_type == self.TargetType.DEPARTMENT and not self.pk:
            return

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    image = models.FileField(upload_to='exam_questions/', blank=True, null=True)
    score = models.IntegerField(default=1)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ('order', 'id')
        unique_together = ('exam', 'order')

    def clean(self):
        if self.score < 1:
            raise ValidationError({'score': 'Оноо 1-ээс их эсвэл тэнцүү байх ёстой.'})

    def __str__(self):
        return f'{self.exam.title} - Q{self.order}'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.text


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='exam_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    is_passed = models.BooleanField(default=False)

    class Meta:
        ordering = ('-started_at',)

    def finish(self):
        if self.completed_at is not None:
            return

        total = 0
        max_total = 0
        for question in self.exam.questions.all():
            max_total += question.score
            response = self.responses.filter(question=question).select_related('selected_choice').first()
            if response and response.selected_choice.is_correct:
                total += question.score

        self.total_score = total
        self.is_passed = total >= self.exam.pass_score
        self.completed_at = timezone.now()
        self.save(update_fields=['total_score', 'is_passed', 'completed_at'])

    def __str__(self):
        return f'{self.employee} - {self.exam}'


class AttemptResponse(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name='attempt_responses',
        null=True,
        blank=True,
    )
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['attempt', 'question'], name='unique_attempt_question_response'),
        ]

    def __str__(self):
        return f'{self.attempt} - Q{self.question.order}'
