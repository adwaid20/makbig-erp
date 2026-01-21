from django.db import models
from adminpanel.models import StudentProfile,User,Course
from .utils import compress_image
# Create your models here.

class WorkType(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='work_types')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.frequency})"


class WorkAssignment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,related_name='work_assignments')
    work_type = models.ForeignKey(WorkType, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student} → {self.work_type}"
    

class WorkSubmission(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'),('verified', 'Verified'),]

    assignment = models.ForeignKey(WorkAssignment,on_delete=models.CASCADE,related_name='submissions')

    submitted_date = models.DateField()
    screenshot = models.ImageField(upload_to='work_screenshots/')

    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='pending')

    reviewed_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='reviewed_submissions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'submitted_date')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.screenshot:
            self.screenshot = compress_image(self.screenshot)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.assignment} | {self.submitted_date}"
