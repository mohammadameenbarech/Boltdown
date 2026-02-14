from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_torrent, name='add_torrent'),
    path('api/status/', views.api_status, name='api_status'),
    path('control/<int:task_id>/<str:action>/', views.control_torrent, name='control_torrent'),
]
