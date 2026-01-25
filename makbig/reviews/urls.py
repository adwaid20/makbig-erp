from django.urls import path
from . import views

urlpatterns = [
    path('staff/reviews/', views.staff_review_list, name='staff_review_list'),
    path('staff/reviews/<int:student_id>/', views.staff_student_review, name='staff_student_review'),
    path('staff/reviews/<int:attendance_id>/edit/', views.staff_edit_completed_review, name='staff_edit_completed_review'),
    path('staff/reviews/payment', views.reviewer_payment_dashboard, name='reviewer_payment_dashboard'),
    path('staff/reviewer-payment/<int:session_id>/toggle/',views.toggle_reviewer_payment,name='toggle_reviewer_payment'),
    # path('staff/reviews/edit/<int:review_id>/', views.staff_edit_review_attendance, name='staff_edit_review_attendance'),


    path('student/reviews/', views.student_review, name='student_review'),
    path('student/reviews/<int:attendance_id>/', views.student_review_detail, name='student_review_detail'),
]
