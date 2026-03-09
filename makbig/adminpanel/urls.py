from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('start', views.get_started, name='get_started'),
    path('staff/login/',views.staff_login,name='staff_login'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/logout/',views.staff_logout,name='staff_logout'),
    path('login/',views.student_login,name='student_login'),
    path('staff/users/', views.staff_students, name='staff_students'),
    path('staff/students/add/', views.add_student, name='add_student'),
    path('staff/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/forgot-password/', views.student_forget_password, name='student_forgot_password'),
    path('student/reset/<uidb64>/<str:token>/', views.student_reset_password, name='student_reset_password'),
    path("student/profile/", views.student_profile, name="student_profile"),
]

