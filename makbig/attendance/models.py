from django.db import models
from adminpanel.models import StudentProfile
from reviews.models import ReviewAttendance
from django.core.exceptions import ValidationError
from django.utils import timezone
# Create your models here.

class AttendanceRecord(models.Model):
    STATUS_CHOICES=[('P','Present'),('A','Absent'),('L','Late')]
    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='attendance_records')
    date=models.DateField()
    status=models.CharField(max_length=1,choices=STATUS_CHOICES,db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
            fields=['student', 'date'],
            name='unique_attendance_per_day')]

        ordering=["-date"]

    def clean(self):
        if self.date > timezone.now().date():
            raise ValidationError("Attendance cannot be recorded for future dates.")
        
        if not self.student:
            raise ValidationError("Student is required")
        
        valid_status=["P","A","L"]
        if self.status not in valid_status:
            raise ValidationError("Invalid attendance status")
    

    def save(self,*args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.email}-{self.date}"






