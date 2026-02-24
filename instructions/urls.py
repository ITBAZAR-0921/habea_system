from django.urls import path

from . import views

urlpatterns = [
    path('', views.instruction_list, name='instruction_list'),
    path('add/', views.instruction_add, name='instruction_add'),
    path('records/', views.instruction_record_list, name='instruction_record_list'),
    path('records/add/', views.instruction_record_add, name='instruction_record_add'),
    path('my/', views.my_instruction_records, name='my_instruction_records'),
    path('my/<int:record_id>/acknowledge/', views.acknowledge_instruction, name='acknowledge_instruction'),
]
