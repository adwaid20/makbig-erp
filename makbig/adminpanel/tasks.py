from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 3})
def send_student_welcome_email(self, email, first_name, temp_password):

    send_mail(
        subject="Welcome to Makbig - Account Created",
        message=(
            f"Hello {first_name},\n\n"
            f"Your account with email: {email} has been created.\n"
            f"Temporary password: {temp_password}\n\n"
            f"you may use the forgot password option in the login page to reset your password"

        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )