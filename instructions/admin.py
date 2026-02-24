from django.contrib import admin

from .models import Instruction, InstructionRecord


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    list_display = ('title', 'validity_days', 'created_at')
    search_fields = ('title',)


@admin.register(InstructionRecord)
class InstructionRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'instruction', 'completed_on', 'valid_until', 'trainer_name')
    list_filter = ('instruction', 'completed_on', 'valid_until')
    search_fields = (
        'employee__first_name',
        'employee__last_name',
        'instruction__title',
        'trainer_name',
    )
