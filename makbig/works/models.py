from django.db import models

# Create your models here.

class WorkAssignment(models.Model):
    WORK_TYPE_CHOICES = [("linkedin", "LinkedIn"),("leetcode", "LeetCode"),("typingclub", "Typing Club"),]
    FREQUENCY_CHOICES = [("daily", "Daily"),("weekly", "Weekly"),]

    title = models.CharField(max_length=100)
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)

    course = models.ForeignKey("adminpanel.Course", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.work_type})"
