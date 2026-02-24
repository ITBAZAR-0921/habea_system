from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Department, Employee, Position


class Training(models.Model):
    class TrainingType(models.TextChoices):
        ORGANIZATION_WIDE = 'organization_wide', 'Бүх ажилтан'
        DEPARTMENT = 'department', 'Хэлтсийн'
        POSITION = 'position', 'Албан тушаалын'
        SPECIFIC_EMPLOYEE = 'specific_employee', 'Тухайлсан ажилтан'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    training_type = models.CharField(max_length=32, choices=TrainingType.choices)

    departments = models.ManyToManyField(Department, blank=True, related_name='trainings')
    positions = models.ManyToManyField(Position, blank=True, related_name='trainings')
    employees = models.ManyToManyField(Employee, blank=True, related_name='target_trainings')

    start_date = models.DateField()
    end_date = models.DateField()

    trainer_name = models.CharField(max_length=255)
    required = models.BooleanField(default=False)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_trainings')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created_at',)

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('Сургалтын дуусах огноо эхлэх огнооноос хойш байх ёстой.')

    def __str__(self):
        return self.title


class TrainingMaterial(models.Model):
    class MaterialType(models.TextChoices):
        IMAGE = 'image', 'Зураг'
        PDF = 'pdf', 'PDF'
        TEXT = 'text', 'Текст'

    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=16, choices=MaterialType.choices)

    file = models.FileField(upload_to='training_materials/', blank=True, null=True)
    text_content = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

    def clean(self):
        text_value = (self.text_content or '').strip()
        if self.material_type in {self.MaterialType.IMAGE, self.MaterialType.PDF}:
            if not self.file:
                raise ValidationError({'file': 'Энэ төрлийн материалд файл заавал оруулна.'})
            if text_value:
                raise ValidationError({'text_content': 'Image/PDF материалд текст агуулга хоосон байна.'})

        if self.material_type == self.MaterialType.TEXT:
            if not text_value:
                raise ValidationError({'text_content': 'Text материалд агуулга заавал оруулна.'})
            if self.file:
                raise ValidationError({'file': 'Text материалд файл оруулахгүй.'})

    def __str__(self):
        return f'{self.training.title} - {self.title}'


class TrainingParticipation(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = 'assigned', 'Хуваарилагдсан'
        ATTENDED = 'attended', 'Суусан'
        COMPLETED = 'completed', 'Дууссан'
        FAILED = 'failed', 'Тэнцээгүй'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='training_participations')
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='participations')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ASSIGNED)
    score = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'training'], name='unique_employee_training_participation'),
        ]
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status != self.Status.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.employee} - {self.training}'
