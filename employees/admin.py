
# Register your models here.
from django.contrib import admin
from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "department",
        "position",
        "is_head",
    )
    list_filter = ("department", "is_head")
    search_fields = ("last_name", "first_name", "register")
