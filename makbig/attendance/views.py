import calendar
from datetime import date, datetime
from .services import AttendanceService



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Sum

from adminpanel.models import StudentProfile,Course
from .models import AttendanceRecord
from penalties.models import Penalty
from django.shortcuts import get_object_or_404
from django.contrib import messages




def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_student_user(user):
    return user.is_authenticated and user.is_student


@login_required
@user_passes_test(is_admin_user,login_url='staff_login')
def attendance_session(request):

    selected_course = request.GET.get("course")

    date_str = request.GET.get("date")

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        selected_date = date.today()


    students = AttendanceService.get_students(selected_course)

    existing_attendance = AttendanceService.get_existing_attendance(
        students,
        selected_date
    )

    existing_fines = AttendanceService.get_existing_fines(
        students,
        selected_date
    )


    if request.method == "POST" and request.POST.get("action") == "save_attendance":

        try:
            AttendanceService.save_attendance(
                request,
                students,
                selected_date
            )

        except ValueError as e:
            messages.error(request, str(e))

        return redirect(f"/attendance/session/?date={selected_date}")

    month_days, attendance_dates = AttendanceService.get_calendar_data(selected_date)
    day_summary = {"P": 0, "A": 0, "L": 0}
    for record in existing_attendance.values():
        if record.status in day_summary:
            day_summary[record.status] += 1
            
    return render(
        request,
        "attendance/staff_attendance.html",
        {
            "students": students,
            "courses": Course.objects.all(),
            "selected_date": selected_date,
            "existing_attendance": existing_attendance,
            "existing_fines": existing_fines,
            "month_days":month_days,
            "attendance_map":  attendance_dates,
            "day_summary":day_summary,
            "selected_course": selected_course,
        },
    )
def student_attendance(request):
    student = get_object_or_404(StudentProfile,user=request.user)

    # Attendance records
    records = AttendanceRecord.objects.filter(
        student=student
    ).order_by("-date")

    total = records.count()
    present = records.filter(status="P").count()
    attendance_percent = int((present / total) * 100) if total > 0 else 0

    # ✅ Attendance-related penalties ONLY
    attendance_penalties = Penalty.objects.filter(
        student=student,
        penalty_type__in=["absence", "late"],
        attendance_record__isnull=False
    ).order_by("-created_at")

    total_attendance_fine = attendance_penalties.aggregate(
        total=Sum("amount")
    )["total"] or 0

    context = {
        "records": records,
        "attendance_percent": attendance_percent,
        "total": total,
        "present": present,
        "attendance_penalties": attendance_penalties,
        "total_attendance_fine": total_attendance_fine,
    }

    return render(request, "attendance/student_attendance.html", context)

