from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )

    class Meta:
        ordering = ('name',)

    def clean(self):
        if self.pk and self.parent_id == self.pk:
            raise ValidationError('Department өөрийгөө parent болгож болохгүй.')
        # Prevent circular hierarchy: a node cannot be a child of its descendants.
        ancestor = self.parent
        while ancestor is not None:
            if ancestor.pk == self.pk:
                raise ValidationError('Department шатлал давталттай байж болохгүй.')
            ancestor = ancestor.parent

    def __str__(self):
        return self.name if not self.parent else f'{self.parent} / {self.name}'


class Position(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Location(models.Model):
    class LocationType(models.TextChoices):
        PROVINCE_CENTER = 'province_center', 'Аймгийн төв'
        SOUM = 'soum', 'Сум'

    name = models.CharField(max_length=150)
    type = models.CharField(max_length=32, choices=LocationType.choices)

    class Meta:
        ordering = ('name',)
        unique_together = ('name', 'type')

    def __str__(self):
        return f'{self.get_type_display()} - {self.name}'


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    register = models.CharField(max_length=20, unique=True, blank=True, null=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )

    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_head = models.BooleanField(default=False)

    photo = models.FileField(upload_to='employees/', blank=True)

    hired_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.last_name} {self.first_name}'
