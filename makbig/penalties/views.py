from django.shortcuts import render

# Create your views here.
# here is the penalties app
# now here i want the penalties or fine of each app(attendance, review or late) to be called separately and then add them to total and pay fine option at each leave if the student wants he can pay only review fine now or only attendace fine now as payment is done the money or fine will be reduced and also keep a colomn at the bottom so that the student can raise a ticket and make any clarrfication related to the fine 


from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required, user_passes_test

from adminpanel.models import StudentProfile, Course
from .models import Penalty
from .forms import PenaltyUpdateForm

from django.core.cache import cache
from adminpanel.services import DASHBOARD_CACHE_KEY


def is_staff_user(user):
    return user.is_staff


# ----------------------------------------
# 1️⃣ Dashboard - Course filter + students
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def penalty_dashboard(request):

    courses = Course.objects.all()
    selected_course = request.GET.get('course')

    students = StudentProfile.objects.all()

    if selected_course:
        students = students.filter(course_id=selected_course)

    students = students.annotate(
        total_unpaid=Sum(
            'penalties__amount',
            filter=Q(penalties__is_paid=False)
        )
    )

    context = {
        'courses': courses,
        'students': students,
        'selected_course': selected_course
    }

    return render(request, 'penalties/fines.html', context)


# ----------------------------------------
# 2️⃣ Student Detail Page
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def student_penalty_detail(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    unpaid_penalties = student.penalties.filter(is_paid=False).order_by('-created_at')
    paid_penalties = student.penalties.filter(is_paid=True).order_by('-created_at')

    total_unpaid = unpaid_penalties.aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'student': student,
        'unpaid_penalties': unpaid_penalties,
        'paid_penalties': paid_penalties,
        'total_unpaid': total_unpaid
    }

    return render(request, 'penalties/student_detail.html', context)


# ----------------------------------------
# 3️⃣ Edit Penalty Amount
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def edit_penalty(request, penalty_id):

    penalty = get_object_or_404(Penalty, id=penalty_id)

    if request.method == 'POST':
        form = PenaltyUpdateForm(request.POST, instance=penalty)
        if form.is_valid():
            form.save()

            cache.delete(DASHBOARD_CACHE_KEY)

            return redirect('student_detail', student_id=penalty.student.id)
    else:
        form = PenaltyUpdateForm(instance=penalty)

    return render(request, 'penalties/edit_penalty.html', {
        'form': form,
        'penalty': penalty
    })


# ----------------------------------------
# 4️⃣ Mark Penalty as Paid
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def mark_penalty_paid(request, penalty_id):

    penalty = get_object_or_404(Penalty, id=penalty_id)

    penalty.is_paid = True
    penalty.save()
    
    cache.delete(DASHBOARD_CACHE_KEY)

    return redirect('student_detail', student_id=penalty.student.id)