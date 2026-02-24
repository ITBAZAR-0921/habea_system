from django.urls import path

from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('upload/', views.employee_upload, name='employee_upload'),
]
