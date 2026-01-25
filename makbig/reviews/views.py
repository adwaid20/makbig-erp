from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from adminpanel.models import StudentProfile,Course
from penalties.models import Penalty
from .models import ReviewAttendance,ReviewSession
from django.contrib import messages
from .forms import ReviewAttendanceForm,ReviewSessionForm
from django.db.models import Sum
from penalties.forms import PenaltyForm
from reviewtickets.models import ReviewTicket
from django.db.models import Count



# Create your views here.


def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user, login_url='staff_login')
def staff_review_list(request):
    courses=Course.objects.all()
    selected_course=request.GET.get('course')
    students=StudentProfile.objects.select_related('user','course')
    if selected_course:
        students=students.filter(course_id=selected_course)
    
    # pending_tickets = ReviewTicket.objects.filter(status='pending')

    return render(request,'reviews/staff_review_list.html',{
        'courses':courses,
        'students':students,
        'selected_course':selected_course,
        # 'pending_tickets':pending_tickets
    })




@login_required(login_url='staff_login')
@user_passes_test(is_staff_user, login_url='staff_login')
def staff_student_review(request, student_id):


    courses = Course.objects.all()
    selected_course = request.GET.get('course')

    student = get_object_or_404(StudentProfile, id=student_id)

    total_fine = Penalty.objects.filter(student=student).aggregate(total=Sum('amount'))['total'] or 0

    # if selected_course and str(student.course.id) != selected_course:
    #     return redirect(f"{request.path}?course={student.course.id}")
    

    upcoming_review = ReviewAttendance.objects.filter(student=student,status__in=['eligible','not_eligible']).select_related('session').first()

    # ================= REVIEW TICKETS (ADMIN VIEW) =================
    pending_ticket = None
    resolved_tickets = []

    if upcoming_review:
        pending_ticket = ReviewTicket.objects.filter(
            review_attendance=upcoming_review,status='pending'
        ).order_by('-created_at').first()

        resolved_tickets = ReviewTicket.objects.filter(
        review_attendance=upcoming_review,
        status__in=['resolved','rejected']
        ).order_by('-created_at')


    existing_fine = Penalty.objects.filter(student=student,penalty_type='review').first()


    past_reviews = ReviewAttendance.objects.filter(student=student,status__in=['pass','fail']).select_related('session').order_by('-session__scheduled_date')

    session_form = ReviewSessionForm(instance=upcoming_review.session if upcoming_review else None)
    
    attendance_form = ReviewAttendanceForm(instance=upcoming_review)


    if request.method == 'POST':
        session_form=ReviewSessionForm(request.POST,instance=upcoming_review.session if upcoming_review else None)
        attendance_form=ReviewAttendanceForm(request.POST,instance=upcoming_review)

        if session_form.is_valid() and attendance_form.is_valid():

             # DELETE any existing upcoming reviews permanently
            # ReviewAttendance.objects.filter(student=student,status__in=['eligible', 'not_eligible']).delete()

            session=session_form.save(commit=False)
            session.course=student.course
            session.save()

            attendance = attendance_form.save(commit=False)
            attendance.student = student
            attendance.session = session
            attendance.save()

            # cancel previous upcoming reviews
            # ReviewAttendance.objects.filter(
            #     student=student,
            #     status__in=['eligible', 'not_eligible']
            #     ).exclude(id=attendance.id).update(status='cancelled')

            fine_amount = request.POST.get('fine_amount')
            fine_reason = request.POST.get('fine_reason')

            Penalty.objects.filter(review_attendance=attendance).delete()

            if fine_amount:
                Penalty.objects.create(student=student,
                review_attendance=attendance,
                
                penalty_type= 'review',
                amount= fine_amount,
                reason= fine_reason,
                created_by= request.user,
                )
            messages.success(request,"Review saved sucessfully")

            return redirect(f"{request.path}?course={student.course.id}")

    return render(request,'reviews/staff_student_review.html',{'courses':courses,'selected_course':selected_course,'student':student,'upcoming_review':upcoming_review,'past_reviews':past_reviews,'session_form':session_form,'attendance_form':attendance_form,'existing_fine': existing_fine,'total_fine': total_fine,'pending_ticket': pending_ticket,
    'resolved_tickets': resolved_tickets,
})




@login_required(login_url='staff_login')
@user_passes_test(is_staff_user, login_url='staff_login')
def staff_edit_completed_review(request, attendance_id):

    review = get_object_or_404(
        ReviewAttendance,
        id=attendance_id,
        status__in=['pass', 'fail']   # 🔒 only completed reviews
    )

    penalty = Penalty.objects.filter(
    review_attendance=review,
    penalty_type='review'
        ).first()

    penalty_form = PenaltyForm(instance=penalty)


    session_form = ReviewSessionForm(
        instance=review.session
    )

    attendance_form = ReviewAttendanceForm(
        instance=review
    )

    if request.method == 'POST':
        session_form = ReviewSessionForm(
            request.POST,
            instance=review.session
        )
        attendance_form = ReviewAttendanceForm(
            request.POST,
            instance=review
        )

        penalty_form = PenaltyForm(request.POST, instance=penalty)

        if session_form.is_valid() and attendance_form.is_valid():
            session_form.save()
            attendance_form.save()

            penalty_obj = penalty_form.save(commit=False)

            if penalty_form.cleaned_data.get('amount'):
                penalty_obj.student = review.student
                penalty_obj.review_attendance = review
                penalty_obj.penalty_type = 'review'
                penalty_obj.created_by = request.user
                penalty_obj.save()
            else:
                Penalty.objects.filter(
                review_attendance=review,penalty_type='review').delete()

            messages.success(
                request,
                "Completed review updated successfully."
            )

            return redirect(
                f"/staff/reviews/{review.student.id}/?course={review.student.course.id}"
            )

    return render(
        request,
        'reviews/staff_edit_completed_review.html',
        {
            'review': review,
            'session_form': session_form,
            'attendance_form': attendance_form,
            'penalty_form': penalty_form,
        }
    )



@login_required(login_url='staff_login')
@user_passes_test(is_staff_user, login_url='staff_login')
def reviewer_payment_dashboard(request):
    sessions = (
        ReviewSession.objects.filter(student_reviews__status__in=['pass','fail'])
        .select_related('course').prefetch_related('student_reviews__student__user').distinct()
        .order_by('reviewer_name', '-scheduled_date'))

    return render(request,'reviews/reviewer_payment_dashboard.html',{'sessions': sessions})


@login_required(login_url='staff_login')
@user_passes_test(is_staff_user, login_url='staff_login')
def toggle_reviewer_payment(request, session_id):
    session = get_object_or_404(ReviewSession, id=session_id)
    session.is_paid = not session.is_paid
    session.save()
    return redirect('reviewer_payment_dashboard')





#student side
from reviewtickets.models import ReviewTicket

@login_required
def student_review(request):
    if not request.user.is_student:
        messages.error(request, "Access denied.")
        return redirect('home')

    student = get_object_or_404(StudentProfile, user=request.user)

    total_fine = Penalty.objects.filter(
        student=student
    ).aggregate(total=Sum('amount'))['total'] or 0

    upcoming_review = ReviewAttendance.objects.filter(
        student=student,
        status__in=['eligible', 'not_eligible']
    ).select_related('session').first()

    completed_reviews = ReviewAttendance.objects.filter(
        student=student,
        status__in=['pass', 'fail']
    ).select_related('session').order_by('-session__scheduled_date')

    upcoming_fine = None
    if upcoming_review:
        upcoming_fine = Penalty.objects.filter(
            student=student,
            review_attendance=upcoming_review,
            penalty_type='review'
        ).first()
    

    tickets = []
    pending_ticket = None

    if upcoming_review:
        tickets = list(
            ReviewTicket.objects.filter(
                student=student,
                review_attendance=upcoming_review
            ).order_by('created_at')
        )

        pending_ticket = next(
            (t for t in tickets if t.status == 'pending'),
            None
        )

    context = {
        'total_fine': total_fine,
        'upcoming_review': upcoming_review,
        'completed_reviews': completed_reviews,
        'tickets': tickets,                 
        'pending_ticket': pending_ticket,   
        'upcoming_fine': upcoming_fine,
    }

    return render(request, 'reviews/student_review.html', context)



def student_review_detail(request,attendance_id):
    if not request.user.is_student:
        messages.error(request,"Access denied")
        return redirect('home')
    
    review=get_object_or_404(ReviewAttendance,id=attendance_id,student__user=request.user)

    return render(request,'reviews/student_review_detail.html',{'review':review})





















# @login_required(login_url='staff_login')
# @user_passes_test(is_staff_user, login_url='staff_login')
# def staff_student_review(request,student_id):
#     student= get_object_or_404(StudentProfile,id=student_id)
#     reviews=ReviewAttendance.objects.filter(student=student).select_related('session').order_by('-session_date')
#     return render(request,'reviews/staff_student_review.html',{
#         'student':student,
#         'reviews':reviews,
#     })

# @login_required(login_url='staff_login')
# @user_passes_test(is_staff_user, login_url='staff_login')
# def staff_edit_review(request, review_id):
#     """
#     Edit any review while preserving course context.
#     """

#     courses = Course.objects.all()
#     selected_course = request.GET.get('course')

#     review = get_object_or_404(ReviewAttendance,id=review_id)

#     session_form = ReviewSessionForm(instance=review.session)

#     attendance_form = ReviewAttendanceForm(instance=review)

#     if request.method == 'POST':

#         session_form = ReviewSessionForm(request.POST,instance=review.session)

#         attendance_form = ReviewAttendanceForm(request.POST,instance=review)

#         if session_form.is_valid() and attendance_form.is_valid():
#             session_form.save()
#             attendance_form.save()

#             messages.success(request,"Review updated successfully.")

#             return redirect(f"/reviews/student/{review.student.id}/?course={review.student.course.id}")

#     return render(request,'reviews/staff_edit_review.html',{
#             'courses': courses,
#             'selected_course': selected_course,
#             'review': review,
#             'session_form': session_form,
#             'attendance_form': attendance_form
#         }
#     )


  
# @login_required(login_url='staff_login')
# @user_passes_test(is_staff_user, login_url='staff_login')
# def staff_edit_review_attendance(request, review_id):

#     review = get_object_or_404(ReviewAttendance, id=review_id)

#     if request.method == 'POST':
#         review.score = request.POST.get('score')
#         review.remarks = request.POST.get('remarks')
#         review.status = request.POST.get('status')
#         review.save()

#         messages.success(request, "Review updated.")
#         return redirect('staff_student_review', student_id=review.student.id)

#     return render(request, 'reviews/staff_edit_review_attendance.html',{
#         'review': review })