from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_works, name='student_works'),
    path('submit/<int:assignment_id>/', views.submit_work, name='submit_work'),
    # path('admin-review/', views.review_submissions, name='review_submissions'),
    # path('verify/<int:submission_id>/', views.verify_submission, name='verify_submission'),
    path('manage/<int:work_id>/submissions/',views.work_submissions,name='work_submissions'),
    path('submission/<int:submission_id>/update/',views.update_submission_status,name='update_submission_status'),
    path('manage/', views.manage_works, name='manage_works'),
    path('student/works/', views.student_works, name='student_works'),
    path('submit-work/<int:assignment_id>/', views.submit_work, name='submit_work'),



]
