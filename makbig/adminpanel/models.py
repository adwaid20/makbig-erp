from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
# Create your models here.
class User(AbstractUser):
    email=models.EmailField(unique=True,db_index=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    is_student=models.BooleanField(default=False)

    def clean(self):
        if self.is_student and self.is_staff:
            raise ValidationError("User cannot be both student and staff.")


    def __str__(self):
        return self.email
    

class Course(models.Model):
    name=models.CharField(max_length=200)
    description=models.TextField(blank=True,null=True)
    duration_months=models.IntegerField(default=6)

    def __str__(self):
        return self.name
    
class StudentProfile(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    course=models.ForeignKey(Course,on_delete=models.PROTECT)
    enrollment_date=models.DateField(auto_now_add=True)
    progress_percent=models.DecimalField(max_digits=5, decimal_places=2, default=0)


    def __str__(self):
        return self.user.email

    def total_fine(self):
        return self.penalties.aggregate(total=Sum('amount'))['total'] or 0


    





# class Week(models.Model):
#     STATUS_CHOICES=(
#         ('active','Active'),
#         ('pending','Pending'),
#         ('completed','Completed'),
#     )
#     student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE)
#     course=models.ForeignKey(Course, on_delete=models.CASCADE)
#     current_week=models.IntegerField()
#     status=models.CharField(max_length=20,choices=STATUS_CHOICES)
#     review=models.ForeignKey(ReviewSession,on_delete=models.SET_NULL,null=True,blank=True)
#     syllabus=models.TextField(null=True,blank=True)

#     def __str__(self):
#         return f"Week{self.current_week} - {self.student.user.email}"
    

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('open','Open'),
        ('handled','Handled'),
    )

    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE)
    reason=models.TextField()
    preferred_date= models.DateField(null=True, blank=True)
    status=models.CharField(max_length=50,choices=STATUS_CHOICES, default='open')

    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket-{self.student.user.email}"
    




    











# makbig/
#     adminpanel/          ← contains ALL models (User, Student, Course, Review, Week, Work, Ticket)
#     attendance/          ← views + urls only
#     review/              ← views + urls only
#     work/                ← views + urls only
#     templates/
#     static/

