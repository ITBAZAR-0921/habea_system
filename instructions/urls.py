from django.urls import path
from . import views

urlpatterns = [
    path('', views.instruction_list, name='instruction_list'),
    path('add/', views.instruction_add, name='instruction_add'),
]