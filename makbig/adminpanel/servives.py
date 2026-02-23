from .models import User, StudentProfile
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings


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
