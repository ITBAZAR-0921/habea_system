from datetime import timedelta

from django.db import models
from django.utils import timezone

from employees.models import Employee


class Instruction(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='instructions/', blank=True, null=True)
    validity_days = models.PositiveIntegerField(
        default=365,
        help_text='Зааварчилгаа хэдэн хоног хүчинтэй байх хугацаа',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class InstructionRecord(models.Model):
    class Status(models.TextChoices):
        VALID = 'valid', 'Хүчинтэй'
        DUE_SOON = 'due_soon', 'Удахгүй дуусна'
        OVERDUE = 'overdue', 'Хугацаа дууссан'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='instruction_records')
    instruction = models.ForeignKey(Instruction, on_delete=models.CASCADE, related_name='records')
    completed_on = models.DateField()
    valid_until = models.DateField(blank=True)
    trainer_name = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('valid_until', '-created_at')
        unique_together = ('employee', 'instruction', 'completed_on')

    def save(self, *args, **kwargs):
        if not self.valid_until:
            self.valid_until = self.completed_on + timedelta(days=self.instruction.validity_days)
        super().save(*args, **kwargs)

    @property
    def status(self):
        today = timezone.localdate()
        if self.valid_until < today:
            return self.Status.OVERDUE
        if self.valid_until <= today + timedelta(days=30):
            return self.Status.DUE_SOON
        return self.Status.VALID

    def __str__(self):
        return f'{self.employee} - {self.instruction}'
