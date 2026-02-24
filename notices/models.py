from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from employees.models import Department, Employee, Position


class Notice(models.Model):
    class NoticeType(models.TextChoices):
        ORGANIZATION_WIDE = 'organization_wide', 'Бүх ажилтан'
        DEPARTMENT = 'department', 'Хэлтсийн'
        POSITION = 'position', 'Албан тушаалын'
        SPECIFIC_EMPLOYEE = 'specific_employee', 'Тухайлсан ажилтан'

    title = models.CharField(max_length=255)
    content = models.TextField()
    notice_type = models.CharField(max_length=32, choices=NoticeType.choices)

    departments = models.ManyToManyField(Department, blank=True, related_name='notices')
    positions = models.ManyToManyField(Position, blank=True, related_name='notices')
    employees = models.ManyToManyField(Employee, blank=True, related_name='notices')

    requires_acknowledgement = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_notices')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Мэдэгдэл'
        verbose_name_plural = 'Мэдэгдлүүд'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.title} ({self.get_notice_type_display()})'


class NoticeRead(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notice_reads')
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='reads')
    read_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Мэдэгдэл уншилт'
        verbose_name_plural = 'Мэдэгдэл уншилтууд'
        constraints = [
            models.UniqueConstraint(fields=['employee', 'notice'], name='unique_employee_notice_read'),
        ]
        ordering = ('-read_at',)

    def save(self, *args, **kwargs):
        if self.acknowledged and self.acknowledged_at is None:
            self.acknowledged_at = timezone.now()
        if not self.acknowledged:
            self.acknowledged_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.employee} - {self.notice}'
