from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('tasks/', views.task_list, name='tasks'),
    path('add/', views.add_task, name='add_task'),
    path('delete/<int:id>/', views.delete_task, name='delete'),
    path('edit/<int:id>/', views.edit_task, name='edit'),
    path('complete/<int:id>/', views.complete_task, name='complete'),
    path('profile/', views.profile, name='profile'),
    path('monthly/', views.monthly_planner, name='monthly_planner'),
]