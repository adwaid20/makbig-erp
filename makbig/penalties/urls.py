from django.urls import path
from . import views

# app_name = "penalties"

urlpatterns = [
    path('', views.penalty_dashboard, name='fines'),
    path('student/<int:student_id>/', views.student_penalty_detail, name='student_detail'),
    path('edit/<int:penalty_id>/', views.edit_penalty, name='edit_penalty'),
    path('mark-paid/<int:penalty_id>/', views.mark_penalty_paid, name='mark_paid'),
]