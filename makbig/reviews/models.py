from django.db import models
from adminpanel.models import StudentProfile,Course
from django.db.models import Q



# Create your models here.


class ReviewSession(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE,related_name='review_sessions')
    created_at=models.DateTimeField(auto_now_add=True)
    scheduled_date=models.DateField()
    review_link=models.CharField(max_length=2550,blank=True,null=True)
    reviewer_name=models.CharField(max_length=250,blank=True,null=True)
    review_name=models.CharField(max_length=100)

    def __str__(self):
        return f"{self.course.name} | {self.scheduled_date}"
    


class ReviewAttendance(models.Model):
    STATUS_CHOICES=(
        ('eligible','Eligible'),
        ('not_eligible', 'Not Eligible'),
        ('pass','Pass'),
        ('fail','Fail'),
    )

    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='reviews')
    remarks=models.CharField(max_length=3550,null=True,blank=True)
    score=models.IntegerField(null=True,blank=True)
    session=models.ForeignKey(ReviewSession,on_delete=models.CASCADE,related_name='student_reviews')
    status=models.CharField(max_length=50, choices=STATUS_CHOICES,default='eligible')
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student'],
                condition=Q(status__in=['eligible', 'not_eligible']),
                name='one_active_upcoming_review_per_student'
            )
        ]


    def __str__(self):
        return f"Review -{self.student.user.email}"
    



