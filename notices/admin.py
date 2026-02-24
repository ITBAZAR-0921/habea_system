from django.contrib import admin

from .models import Notice, NoticeRead


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'notice_type', 'created_by', 'created_at', 'is_active')
    list_filter = ('notice_type', 'is_active', 'created_at')
    search_fields = ('title', 'content', 'created_by__username')
    filter_horizontal = ('departments', 'positions', 'employees')


@admin.register(NoticeRead)
class NoticeReadAdmin(admin.ModelAdmin):
    list_display = ('employee', 'notice', 'read_at', 'acknowledged', 'acknowledged_at')
    list_filter = ('acknowledged', 'read_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'notice__title')
