from .models import ReviewTicket


def ticket_notifications(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = ReviewTicket.objects.filter(
            status='pending',
            is_seen=False
        ).count()
        return {'ticket_notification_count': count}
    return {}
