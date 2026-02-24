from django.contrib import admin

from .models import Instruction, InstructionRecord


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    list_display = ('title', 'instruction_type', 'validity_days', 'created_at')
    list_filter = ('instruction_type',)
    search_fields = ('title',)


@admin.register(InstructionRecord)
class InstructionRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'instruction', 'completed_date', 'next_due_date', 'acknowledged', 'acknowledged_date')
    list_filter = ('instruction', 'acknowledged', 'next_due_date')
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'instruction__title',
    )
