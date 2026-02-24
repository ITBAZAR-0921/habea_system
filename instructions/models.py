from datetime import timedelta

from django.db import models
from django.utils import timezone

from employees.models import Employee


class Instruction(models.Model):
    class InstructionType(models.TextChoices):
        ORGANIZATION = 'organization', 'Байгууллагын нийтлэг'
        DEPARTMENT = 'department', 'Хэлтсийн'
        POSITION = 'position', 'Албан тушаалын'

    title = models.CharField(max_length=200)
    description = models.TextField()
    instruction_type = models.CharField(
        max_length=32,
        choices=InstructionType.choices,
        default=InstructionType.ORGANIZATION,
    )
    file = models.FileField(upload_to='instructions/', blank=True, null=True)
    validity_days = models.PositiveIntegerField(
        default=365,
        help_text='Зааварчилгаа хэдэн хоног хүчинтэй байх хугацаа',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


class InstructionRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='instruction_records')
    instruction = models.ForeignKey(Instruction, on_delete=models.CASCADE, related_name='records')
    completed_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(default=timezone.localdate)
    acknowledged = models.BooleanField(default=False)
    acknowledged_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('next_due_date', '-created_at')
        unique_together = ('employee', 'instruction')

    def save(self, *args, **kwargs):
        base_date = self.completed_date or timezone.localdate()
        if self.instruction_id:
            self.next_due_date = base_date + timedelta(days=self.instruction.validity_days)

        if not self.acknowledged:
            self.acknowledged_date = None
        elif self.acknowledged and self.acknowledged_date is None:
            self.acknowledged_date = timezone.localdate()

        super().save(*args, **kwargs)

    @property
    def status(self):
        today = timezone.localdate()
        if self.next_due_date < today:
            return 'overdue'
        if self.next_due_date <= today + timedelta(days=30):
            return 'due_soon'
        return 'valid'

    def __str__(self):
        return f'{self.employee} - {self.instruction}'
