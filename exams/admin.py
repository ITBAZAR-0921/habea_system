from django.contrib import admin

from .models import AttemptResponse, Choice, Exam, ExamAttempt, Question


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'order', 'text', 'score')
    list_filter = ('exam',)
    search_fields = ('text',)
    inlines = [ChoiceInline]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'exam_type',
        'target_type',
        'duration_minutes',
        'pass_score',
        'is_active',
        'created_by',
        'created_at',
    )
    list_filter = ('exam_type', 'target_type', 'is_active')
    search_fields = ('title',)
    filter_horizontal = ('departments', 'positions')


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    list_filter = ('is_correct', 'question__exam')
    search_fields = ('text',)


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('exam', 'employee', 'started_at', 'completed_at', 'total_score', 'is_passed')
    list_filter = ('is_passed', 'exam')


@admin.register(AttemptResponse)
class AttemptResponseAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_choice', 'answered_at')
    list_filter = ('question__exam',)
