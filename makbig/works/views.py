from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from works.models import WorkAssignment,WorkSubmission,WorkType
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from adminpanel.models import StudentProfile,Course

# Create your views here.


@login_required
def submit_work(request, assignment_id):
    assignment = get_object_or_404(
        WorkAssignment,
        id=assignment_id,
        student=request.user.studentprofile
    )

    if WorkSubmission.objects.filter(assignment=assignment).exists():
        return redirect('student_works')

    if request.method == 'POST':
        screenshot = request.FILES.get('screenshot')

        if screenshot:
            WorkSubmission.objects.create(
                assignment=assignment,
                submitted_date=timezone.now().date(),
                screenshot=screenshot
            )

        return redirect('student_works')

    return render(
        request,
        'works/submit_work.html',
        {'assignment': assignment}
    )


# @staff_member_required
# def review_submissions(request):
#     submissions = WorkSubmission.objects.all()
#     return render(request, 'works/admin_work_review.html', {
#         'submissions': submissions
#     })

# @staff_member_required
# def verify_submission(request, submission_id):
#     submission = get_object_or_404(WorkSubmission, id=submission_id)

#     submission.status = 'verified'
#     submission.reviewed_by = request.user
#     submission.reviewed_at = timezone.now()
#     submission.save()

#     return redirect('review_submissions')


@staff_member_required
def manage_works(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        frequency = request.POST.get('frequency')
        course_id = request.POST.get('course')

        if name and frequency and course_id:
            # 1. Create work
            new_work = WorkType.objects.create(
                name=name,
                frequency=frequency,
                course_id=course_id
            )

            # 2. ASSIGN TO EXISTING STUDENTS
            students = StudentProfile.objects.filter(course_id=course_id)

            for student in students:
                WorkAssignment.objects.get_or_create(
                    student=student,
                    work_type=new_work
                )

        return redirect('manage_works')

    works = WorkType.objects.select_related('course').all()
    courses = Course.objects.all()

    return render(request, 'works/manage_works.html', {
        'works': works,
        'courses': courses
    })


@staff_member_required
def work_submissions(request, work_id):
    work = get_object_or_404(WorkType, id=work_id)

    assignments = WorkAssignment.objects.filter(
        work_type=work
    ).select_related('student__user')

    submissions = {
        s.assignment_id: s
        for s in WorkSubmission.objects.filter(
            assignment__work_type=work
        )
    }

    data = []
    for assignment in assignments:
        submission = submissions.get(assignment.id)
        data.append({
            'student': assignment.student,
            'assignment': assignment,
            'submission': submission
        })

    return render(request, 'works/work_submissions.html', {
        'work': work,
        'data': data
    })


@staff_member_required
def update_submission_status(request, submission_id):
    submission = get_object_or_404(WorkSubmission, id=submission_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'verified']:
            submission.status = status
            submission.reviewed_by = request.user
            submission.reviewed_at = timezone.now()
            submission.save()

    return redirect(
        'work_submissions',
        work_id=submission.assignment.work_type.id
    )

@login_required
def student_works(request):
    student = get_object_or_404(StudentProfile, user=request.user)

    assignments = (
        WorkAssignment.objects
        .filter(student=student)
        .select_related('work_type')
    )

    submissions = {
        s.assignment_id: s
        for s in WorkSubmission.objects.filter(
            assignment__student=student
        )
    }

    data = []
    for assignment in assignments:
        submission = submissions.get(assignment.id)
        data.append({
            'assignment': assignment,
            'submission': submission,
            'is_pending': submission is None
        })

    return render(
        request,
        'works/student_works.html',
        {'data': data}
    )
