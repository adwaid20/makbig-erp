from datetime import date
from django.db import transaction
from django.utils import timezone

from adminpanel.models import StudentProfile
from penalties.models import Penalty
from .models import AttendanceRecord


class AttendanceService:


    @staticmethod
    def get_calendar_data(selected_date):
        import calendar
    
        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        month_days = cal.monthdatescalendar(selected_date.year, selected_date.month)

        last_day = calendar.monthrange(selected_date.year, selected_date.month)[1]
        attendance_dates = set(
            AttendanceRecord.objects.filter(
            date__gte=selected_date.replace(day=1),
            date__lte=selected_date.replace(day=last_day)
        ).values_list("date", flat=True).distinct()
    )

        return month_days, attendance_dates
    
    @staticmethod
    def get_students(course_id=None):
        students = StudentProfile.objects.select_related("user", "course")

        if course_id:
            students = students.filter(course_id=course_id)

        return students


    @staticmethod
    def get_existing_attendance(students, selected_date):
        return {
            record.student_id: record
            for record in AttendanceRecord.objects.filter(
                student__in=students,
                date=selected_date
            )
        }


    @staticmethod
    def get_existing_fines(students, selected_date):
        return {
            fine.student_id: fine
            for fine in Penalty.objects.filter(
                student__in=students,
                attendance_record__date=selected_date
            )
        }


    @staticmethod
    @transaction.atomic
    def save_attendance(request, students, selected_date):

        if selected_date > timezone.now().date():
            raise ValueError("Attendance cannot be recorded for future dates.")

        for student in students:

            status = request.POST.get(f"status_{student.id}")
            fine_input = request.POST.get(f"fine_{student.id}")
            remark = request.POST.get(f"remark_{student.id}", "").strip()

            if not status:
                continue

            fine_amount = None

            if fine_input:
                try:
                    fine_amount = float(fine_input)

                    if fine_amount < 0:
                        fine_amount = None

                    if fine_amount > 10000:
                        fine_amount = 10000

                except (ValueError, TypeError):
                    fine_amount = None


            attendance, _ = AttendanceRecord.objects.update_or_create(
                student=student,
                date=selected_date,
                defaults={"status": status}
            )


            Penalty.objects.filter(
                student=student,
                attendance_record__date=selected_date
            ).delete()


            if fine_amount:
                Penalty.objects.create(
                    student=student,
                    attendance_record=attendance,
                    penalty_type="late" if status == "L" else "absence",
                    amount=fine_amount,
                    reason=remark or "Attendance penalty",
                    created_by=request.user
                )