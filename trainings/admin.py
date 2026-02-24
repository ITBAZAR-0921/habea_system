from django.contrib import admin

from .models import Training, TrainingMaterial, TrainingParticipation


class TrainingMaterialInline(admin.TabularInline):
    model = TrainingMaterial
    extra = 1


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'training_type', 'start_date', 'end_date', 'required', 'is_active', 'created_by')
    list_filter = ('training_type', 'required', 'is_active', 'start_date')
    search_fields = ('title', 'trainer_name', 'created_by__username')
    filter_horizontal = ('departments', 'positions', 'employees')
    inlines = [TrainingMaterialInline]


@admin.register(TrainingMaterial)
class TrainingMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'training', 'material_type', 'created_at')
    list_filter = ('material_type',)
    search_fields = ('title', 'training__title')


@admin.register(TrainingParticipation)
class TrainingParticipationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'training', 'status', 'score', 'completed_at')
    list_filter = ('status',)
    search_fields = ('employee__first_name', 'employee__last_name', 'training__title')
