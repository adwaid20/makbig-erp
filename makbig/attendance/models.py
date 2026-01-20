from django.db import models
from adminpanel.models import StudentProfile
from reviews.models import ReviewAttendance
# Create your models here.

class AttendanceRecord(models.Model):
    STATUS_CHOICES=[('P','Present'),('A','Absent'),('L','Late')]
    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='attendance_records')
    date=models.DateField()
    status=models.CharField(max_length=1,choices=STATUS_CHOICES)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
            fields=['student', 'date'],
            name='unique_attendance_per_day')]


    
    def __str__(self):
        return f"{self.student.user.email}-{self.date}"






