from django.contrib import admin
from .models import WorkType, WorkAssignment, WorkSubmission

# Register your models here.

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'frequency', 'is_active')

@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'work_type', 'is_active')

@admin.register(WorkSubmission)
class WorkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'submitted_date', 'status')