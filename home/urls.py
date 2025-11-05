from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('api/student-login/', views.student_login_credentials, name='student_login'),
    path('api/set-admin-session/', views.set_admin_session, name='set_admin_session'),
    path('api/create-test/', views.create_test, name='create_test'),
    path('api/create-student/', views.create_student_with_login, name='create_student'),
    path('api/tests/', views.get_tests, name='get_tests'),
    path('api/students/', views.get_students, name='get_students'),
    path('api/results/', views.get_results, name='get_results'),
    path('api/ranking/admin/', views.get_ranking_admin, name='get_ranking_admin'),  # ✅ Yangi nom
    path('api/ranking/student/', views.get_student_ranking, name='get_student_ranking'),
    
    # Student API
    path('api/test/<int:test_id>/questions/', views.get_test_questions, name='get_test_questions'),
    path('api/submit-test/', views.submit_test, name='submit_test'),
    path('api/my-results/', views.get_student_results, name='get_student_results'),
    path('api/my-activity/', views.get_student_activity, name='get_student_activity'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]