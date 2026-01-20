import calendar
from datetime import date, datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count,Sum

from adminpanel.models import StudentProfile,Course
from .models import AttendanceRecord
from penalties.models import Penalty


@login_required(login_url='/login/')
def attendance_session(request):

    selected_course = request.GET.get("course")
    



    #date selection
    date_str = request.GET.get('date')

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    year = selected_date.year
    month = selected_date.month

    students = StudentProfile.objects.select_related('user', 'course')

    if selected_course:
        students = students.filter(course_id=selected_course)


    
    #load existing attendance
    existing_attendance = {
        record.student_id: record
        for record in AttendanceRecord.objects.filter(date=selected_date)
    }

    
    #load any existing fines
    existing_fines = {
        fine.student_id: fine
        for fine in Penalty.objects.filter(
            student__in=students,
            attendance_record__date=selected_date
        )
    }

   
   #above day summary, count taking of eah day
    day_summary = AttendanceRecord.objects.filter(
        date=selected_date
    ).values('status').annotate(count=Count('id'))

    day_summary_map = {'P': 0, 'A': 0, 'L': 0}
    for item in day_summary:
        day_summary_map[item['status']] = item['count']


    #calender
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)

    month_attendance = AttendanceRecord.objects.filter(
        date__year=year,
        date__month=month
    )

    attendance_map = {}
    for record in month_attendance:
        attendance_map.setdefault(record.date, []).append(record)

    
    #edit, without creating duplicates
    if request.method == 'POST' and request.POST.get('action') == 'save_attendance':
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            fine_amount = request.POST.get(f'fine_{student.id}')
            remark = request.POST.get(f'remark_{student.id}', '').strip()

            if not status:
                continue

            attendance, _ = AttendanceRecord.objects.update_or_create(
                student=student,
                date=selected_date,
                defaults={'status': status}
            )

            #when edited delete the existing fine
            Penalty.objects.filter(
                student=student,
                attendance_record__date=selected_date
            ).delete()

            #create new fines
            if fine_amount:
                Penalty.objects.create(
                    student=student,
                    attendance_record=attendance,
                    penalty_type='late' if status == 'L' else 'absence',
                    amount=fine_amount,
                    reason=remark or 'Attendance penalty',
                    created_by=request.user
                )

        return redirect(f'/attendance/session/?date={selected_date}')

   
    return render(
        request,
        'attendance/staff_attendance.html',
        {
            'students': students,
            'students': students,
            'courses': Course.objects.all(),
            'selected_date': selected_date,
            'existing_attendance': existing_attendance,
            'existing_fines': existing_fines,  
            'day_summary': day_summary_map,
            'month_days': month_days,
            'attendance_map': attendance_map,
        }
    )


def student_attendance(request):
    student = StudentProfile.objects.get(user=request.user)

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

