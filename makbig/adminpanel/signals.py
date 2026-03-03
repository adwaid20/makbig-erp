from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import StudentProfile
from works.models import WorkType, WorkAssignment

@receiver(post_save, sender=StudentProfile,dispatch_uid="assign_works_on_student_creation")
def assign_works_on_student_creation(sender, instance, created, **kwargs):
    if not created:
        return
    
    course = instance.course
    if not course: #fail safe aan , course illand ende course work
        return

    def assign_works():
        works=WorkType.objects.filter(course=instance.course,is_active=True)
        
        assignments=[WorkAssignment(student=instance,work_type=work)
                     for work in works ]
        
        WorkAssignment.objects.bulk_create(assignments)
    
    transaction.on_commit(assign_works)