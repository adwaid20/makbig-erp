from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator,MinValueValidator,MaxValueValidator
from decimal import Decimal



# Create your models here.

name_validator=RegexValidator(regex=r'^[A-Za-z]+$', message="Only alphabetic characters are allowed.")

mobile_validator=RegexValidator(regex=r'^\d{10}$', message="Mobile number must contain only digits and must havee 10 digits")



class User(AbstractUser):
    ROLE_CHOICES = (
    ('superadmin', 'Super Admin'),
    ('staff', 'Staff'),
    ('student', 'Student'),
)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email=models.EmailField(unique=True,db_index=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True,validators=[mobile_validator])
    
    first_name = models.CharField(max_length=100,validators=[name_validator])
    last_name = models.CharField(max_length=100,validators=[name_validator])

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_superadmin(self):                  # ← ADD THIS — used by decorator
        return self.role == 'superadmin'


    def clean(self):
        if self.is_student and self.is_staff:
            raise ValidationError("User cannot be both student and staff.")

    def save(self,*args, **kwargs):
        self.email=self.email.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    

class Course(models.Model):
    name=models.CharField(max_length=200)
    description=models.TextField(blank=True,null=True, max_length=2000)
    duration_months=models.PositiveIntegerField(default=6,validators=[MinValueValidator(1),MaxValueValidator(60)])

    def __str__(self):
        return self.name
    

class StudentProfile(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    course=models.ForeignKey(Course,on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    enrollment_date=models.DateField(auto_now_add=True)
    progress_percent=models.DecimalField(max_digits=5, decimal_places=2, default=0,validators=[MinValueValidator(Decimal('0.00')),MaxValueValidator(Decimal('100.00'))])


    def __str__(self):
        return self.user.email

    def total_fine(self):
        return self.penalties.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')


    





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

