from django.urls import path

from . import views

urlpatterns = [
    path('', views.notice_list, name='notice_list'),
    path('add/', views.notice_create, name='notice_create'),
    path('<int:notice_id>/edit/', views.notice_update, name='notice_update'),
    path('<int:notice_id>/delete/', views.notice_delete, name='notice_delete'),
    path('my/', views.my_notices, name='my_notices'),
    path('my/<int:notice_id>/acknowledge/', views.acknowledge_notice, name='acknowledge_notice'),
]
