from .models import User, StudentProfile
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
    try:
        send_mail(
            subject="Welcome to Makbig-Account Created",
            message=(
                f"Hello {first_name},\n\n"
                f"Your account with email : {email} has been created \n"
                f"The temperory password for login is {temp_password}"
                f"you may use the forgot password option by entering the linked email and set a new password"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
    except Exception:
        pass

    return user


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

        return {
            "active_students": cls.active_students(),
            "total_students": cls.total_students(),
            "present_today": cls.todays_attendance(),
            "absent_today": cls.absent_today(),
            "reviews_this_week": cls.reviews_this_week(),
            "pending_works": cls.pending_works(),
            "unpaid_fines": cls.unpaid_fines(),
        }