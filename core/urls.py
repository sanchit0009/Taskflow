from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Template (frontend) URL patterns
template_urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('projects/', views.project_list_view, name='project_list'),
    path('projects/create/', views.project_create_view, name='project_create'),
    path('projects/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project_delete'),
    path('projects/<int:pk>/members/add/', views.add_member_view, name='add_member'),
    path('projects/<int:pk>/members/<int:user_id>/remove/', views.remove_member_view, name='remove_member'),
    path('projects/<int:project_pk>/tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:pk>/delete/', views.task_delete_view, name='task_delete'),
]

# REST API URL patterns
api_urlpatterns = [
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='api_token'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/dashboard/', views.dashboard_stats_api, name='api_dashboard'),
    path('api/projects/', views.ProjectListCreateAPI.as_view(), name='api_projects'),
    path('api/projects/<int:pk>/', views.ProjectDetailAPI.as_view(), name='api_project_detail'),
    path('api/projects/<int:pk>/members/add/', views.add_member_api, name='api_add_member'),
    path('api/projects/<int:pk>/members/<int:user_id>/remove/', views.remove_member_api, name='api_remove_member'),
    path('api/projects/<int:project_pk>/tasks/', views.TaskListCreateAPI.as_view(), name='api_tasks'),
    path('api/tasks/<int:pk>/', views.TaskDetailAPI.as_view(), name='api_task_detail'),
]

urlpatterns = template_urlpatterns + api_urlpatterns
