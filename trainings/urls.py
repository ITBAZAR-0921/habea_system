from django.urls import path

from . import views

urlpatterns = [
    path('', views.training_list, name='training_list'),
    path('add/', views.training_create, name='training_create'),
    path('<int:training_id>/', views.training_detail, name='training_detail'),
    path('<int:training_id>/edit/', views.training_update, name='training_update'),
    path('<int:training_id>/delete/', views.training_delete, name='training_delete'),
    path('my/', views.my_trainings, name='my_trainings'),
]
