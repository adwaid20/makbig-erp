from django.urls import path
from . import views

urlpatterns = [
    path('session/', views.attendance_session, name='staff_attendance'),
    path("attendance/", views.student_attendance, name="student_attendance"),
]
