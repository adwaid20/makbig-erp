from .models import User, StudentProfile,Course
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from attendance.models import AttendanceRecord
from reviews.models import ReviewAttendance
from works.models import WorkSubmission
from penalties.models import Penalty
from django.db.models import Sum
from django.utils import timezone

from adminpanel.tasks import send_student_welcome_email
from django.db.transaction import on_commit

from django.core.cache import cache

DASHBOARD_CACHE_KEY = "dashboard:summary"
DASHBOARD_CACHE_TIMEOUT = 60

def create_student(data):
    temp_password=get_random_string(8)
    username=data['email']
    email=data['email']
    first_name=data['first_name']
    last_name=data['last_name']
    course=data['course']

    with transaction.atomic():
        user=User.objects.create_user(
            username=email,
            email=email,
            password=temp_password,
            first_name=first_name,
            last_name=last_name,
            is_student=True,
            is_staff=False,
        )

        StudentProfile.objects.create(
            user=user,
            course=course,
            )
        

        on_commit(lambda: send_student_welcome_email.delay(
            email, first_name, temp_password
        ))
    
    invalidate_dashboard_cache()

    return user


def invalidate_dashboard_cache():
    cache.delete(DASHBOARD_CACHE_KEY)



class DashboardService:

    @staticmethod
    def active_students():
        return StudentProfile.objects.filter(is_active=True).only("id").count()

    @staticmethod
    def total_students():
        return StudentProfile.objects.only("id").count()

    @staticmethod
    def todays_attendance():
        today = timezone.localdate()

        return AttendanceRecord.objects.filter(
            date=today,
            status='P'
        ).count()

    @staticmethod
    def absent_today():
        today = timezone.localdate()

        return AttendanceRecord.objects.filter(date=today,status='A').count()

    @staticmethod
    def reviews_this_week():
        week_ago = timezone.now() - timedelta(days=7)

        return ReviewAttendance.objects.filter(created_at__gte=week_ago).count()

    @staticmethod
    def pending_works():
        return WorkSubmission.objects.filter(status='pending').count()

    @staticmethod
    def unpaid_fines():
        fines = Penalty.objects.filter(is_paid=False).aggregate(total=Sum('amount'))
        return fines['total'] or 0
    
    @classmethod
    def get_dashboard_summary(cls):

        cached_data = cache.get(DASHBOARD_CACHE_KEY)

        if cached_data is not None:
            return cached_data
    
        data = {
            "active_students": cls.active_students(),
            "total_students": cls.total_students(),
            "present_today": cls.todays_attendance(),
            "absent_today": cls.absent_today(),
            "reviews_this_week": cls.reviews_this_week(),
            "pending_works": cls.pending_works(),
            "unpaid_fines": cls.unpaid_fines(),
        }

        cache.set(DASHBOARD_CACHE_KEY, data, DASHBOARD_CACHE_TIMEOUT)

        return data


# adminpanel/services.py — ADD AT THE BOTTOM

SUPERADMIN_CACHE_KEY = "superadmin:dashboard_summary"
SUPERADMIN_CACHE_TIMEOUT = 60


def invalidate_superadmin_cache():
    cache.delete(SUPERADMIN_CACHE_KEY)


class SuperAdminDashboardService:

    @classmethod
    def get_dashboard_summary(cls):
        cached = cache.get(SUPERADMIN_CACHE_KEY)
        if cached is not None:
            return cached

        staff_qs = User.objects.filter(is_staff=True, is_superuser=False)
        newest = staff_qs.order_by('-date_joined').first()

        data = {
            'total_staff':    staff_qs.count(),
            'active_staff':   staff_qs.filter(is_active=True).count(),
            'disabled_staff': staff_qs.filter(is_active=False).count(),
            'recent_staff':   list(staff_qs.order_by('-date_joined')[:5]),
            'newest_staff': newest,
            'newest_staff_name': (newest.get_full_name() or newest.username) if newest else "—",
        }

        cache.set(SUPERADMIN_CACHE_KEY, data, SUPERADMIN_CACHE_TIMEOUT)
        return data
    
class CourseService:

    @staticmethod
    def create_course(data):
        return Course.objects.create(**data)

    @staticmethod
    def get_all_courses():
        return Course.objects.all().order_by('-id')