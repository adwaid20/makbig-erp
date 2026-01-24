from django.urls import path
from . import views

urlpatterns = [
    path('staff/tickets/', views.staff_ticket_list, name='staff_ticket_list'),
    path('staff/ticket/<int:ticket_id>/resolve/', views.resolve_ticket, name='resolve_ticket'),
    path('staff/ticket/<int:ticket_id>/reject/', views.reject_ticket, name='reject_ticket'),


    path('student/review/<int:review_id>/ticket/',views.create_or_edit_ticket,name='student_ticket')

]
