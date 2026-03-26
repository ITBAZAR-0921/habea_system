from django.urls import path

from .views import ReportDashboardView, ReportExportView


urlpatterns = [
    path('', ReportDashboardView.as_view(), name='reports'),
    path('export/', ReportExportView.as_view(), name='reports_export'),
]
