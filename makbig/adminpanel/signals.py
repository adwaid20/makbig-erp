from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StudentProfile
from works.models import WorkType, WorkAssignment

@receiver(post_save, sender=StudentProfile)
def assign_works_on_student_creation(sender, instance, created, **kwargs):
    if not created:
        return

    course = instance.course
    if not course:
        return

    works = WorkType.objects.filter(course=course, is_active=True)

    for work in works:
        WorkAssignment.objects.create(student=instance,work_type=work)
