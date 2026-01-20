from django.db import models
from adminpanel.models import StudentProfile
from reviews.models import ReviewAttendance
# Create your models here.

class ReviewTicket(models.Model):
    STATUS_CHOICES=[('pending','Pending'),('resolved','Resolved'),('rejected','Rejected'),]

    student=models.ForeignKey(StudentProfile, on_delete=models.CASCADE,related_name='reviewtickets')

    review_attendance=models.ForeignKey(ReviewAttendance,  on_delete=models.CASCADE, related_name='review_tickets')

    message=models.CharField( max_length=1550)

    status=models.CharField(max_length=10,choices=STATUS_CHOICES,default='pending')

    is_seen=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'review_attendance'],
                condition=models.Q(status='pending'),
                name='one_pending_ticket_per_review'
            )
        ]

    def __str__(self):
        return f"{self.student.user.email} | Review {self.review_attendance.id}"