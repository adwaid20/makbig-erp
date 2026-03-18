from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Course, StudentProfile, Ticket

class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
    )

    # list_filter = (
    #     'is_staff',
    #     'is_superuser',
    #     'is_student',
    # )

    # fieldsets = (
    #     (None, {'fields': ('email', 'password')}),
    #     ('Personal Info', {'fields': ('first_name', 'last_name', 'mobile_number')}),
    #     ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_student')}),
    #     ('Important dates', {'fields': ('last_login', 'date_joined')}),
    # )

    # add_fieldsets = (
    #     (None, {
    #         'classes': ('wide',),
    #         'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_student', 'is_staff'),
    #     }),
    # )



admin.site.register(User, CustomUserAdmin)
admin.site.register(Course)
admin.site.register(StudentProfile)
# admin.site.register(Week)
admin.site.register(Ticket)
# admin.site.register(ReviewSession)
# admin.site.register(ReviewAttendance)
