from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from reviews.models import ReviewAttendance
from .models import ReviewTicket
from .forms import ReviewTicketForm
from adminpanel.models import StudentProfile
# Create your views here.

def staff_ticket_list(request):
    tickets= ReviewTicket.objects.filter(status='pending')

    tickets.update(is_seen=True)

    return render (request,'reviewtickets/staff_ticket_list.html',{'tickets':tickets})


@staff_member_required
def resolve_ticket(request, ticket_id):
    ticket = get_object_or_404(ReviewTicket, id=ticket_id)
    ticket.status = 'resolved'
    ticket.save()
    return redirect('staff_ticket_list')










#students
@login_required
def create_or_edit_ticket(request, review_id):
    if not request.user.is_student:
        messages.error(request, "Access denied.")
        return redirect('home')

    student = get_object_or_404(StudentProfile, user=request.user)
    review = get_object_or_404(ReviewAttendance, id=review_id, student=student)

    all_tickets = ReviewTicket.objects.filter(
        student=student,
        review_attendance=review
    ).order_by('-created_at')

    pending_ticket = all_tickets.filter(status='pending').first()

    # 🔹 Enforce max 2 tickets per review
    if not pending_ticket and all_tickets.count() >= 2:
        messages.info(
            request,
            "You have already raised the maximum number of tickets for this review."
        )
        return redirect('student_review')

    if request.method == 'POST':
        form = ReviewTicketForm(request.POST, instance=pending_ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.student = student
            ticket.review_attendance = review
            ticket.status = 'pending'
            ticket.save()
            messages.success(request, "Ticket submitted successfully.")
            return redirect('student_review')
    else:
        form = ReviewTicketForm(instance=pending_ticket)

    return render(request, 'reviewtickets/student_ticket_form.html', {
        'form': form,
        'review': review,
        'tickets': all_tickets,   # 👈 send history
        'pending_ticket': pending_ticket,
    })