from django.db import models
from adminpanel.models import StudentProfile
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from attendance.models import AttendanceRecord
# Create your models here.


class Penalty(models.Model):

    PENALTY_TYPE_CHOICES = [
        ('late', 'Late Submission'),
        ('absence', 'Absence'),
        ('misconduct', 'Misconduct'),
        ('review', 'Review Related'),
        ('other', 'Other'),
    ]

    student = models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='penalties')

    penalty_type = models.CharField(max_length=20,choices=PENALTY_TYPE_CHOICES)


    reason = models.TextField(blank=True)

    # Optional links (VERY IMPORTANT)
    review_attendance = models.ForeignKey('reviews.ReviewAttendance',on_delete=models.SET_NULL,null=True,blank=True)

    attendance_record = models.ForeignKey(AttendanceRecord,on_delete=models.SET_NULL,null=True,blank=True,related_name='penalties')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_paid = models.BooleanField(default=False)

    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("10000.00"))  # ₹10,000 HARD LIMIT
        ]
    )

    def __str__(self):
        return f"{self.student.user.email} - ₹{self.amount}"
