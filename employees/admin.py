from django.contrib import admin

from .models import Department, Employee, Location, Position


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type')
    list_filter = ('type',)
    search_fields = ('name',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'department', 'position', 'location', 'is_head')
    list_filter = ('department', 'position', 'location', 'is_head')
    search_fields = ('last_name', 'first_name', 'register', 'user__username')
    autocomplete_fields = ('department', 'position', 'location', 'user')
