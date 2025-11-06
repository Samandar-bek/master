from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('', views.index, name='index'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('api/student-login/', views.student_login_credentials, name='student_login'),
    path('api/create-test/', views.create_test, name='create_test'),
    path('api/create-student/', views.create_student_with_login, name='create_student'),
    path('api/tests/', views.get_tests, name='get_tests'),
    path('api/students/', views.get_students, name='get_students'),
    path('api/results/', views.get_results, name='get_results'),
    path('api/ranking-admin/', views.get_ranking_admin, name='ranking_admin'),
    path('api/student-results/', views.get_student_results, name='student_results'),
    path('api/student-ranking/', views.get_student_ranking, name='student_ranking'),
    path('api/test-questions/<int:test_id>/', views.get_test_questions, name='test_questions'),
    path('api/submit-test/', views.submit_test, name='submit_test'),
    path('api/delete-student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('api/delete-test/<int:test_id>/', views.delete_test, name='delete_test'),
]