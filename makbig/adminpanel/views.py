from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from .models import StudentProfile,Course
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .services import create_student, invalidate_dashboard_cache
from django.core.paginator import Paginator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
# Create your views here.
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
# from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django_ratelimit.decorators import ratelimit

from .services import DashboardService,SuperAdminDashboardService,invalidate_superadmin_cache,CourseService
from penalties.models import Penalty
from .forms import StaffLoginForm,StudentLoginForm,AddStudentForm,AddStaffForm,EditStaffForm,CourseForm
from .decorators import superadmin_required


from core.cache_utils import SafeCache
from adminpanel.services import DASHBOARD_CACHE_KEY

User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and user.is_active and (user.is_staff or user.is_superuser)

def is_student_user(user):
    return user.is_authenticated and user.is_student



@never_cache
@ratelimit(key='ip', rate='5/m', block=True)
def staff_login(request):
    if request.method=='POST':
        form=StaffLoginForm(request.POST)
        if form.is_valid():
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']


            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Invalid credentials")
                return render(request, 'adminpanel/login.html', {'form': form})
            

            user=authenticate(request , username=user_obj.username , password=password )

            if user and (user.is_staff or user.is_superuser):
                login(request, user)
                print("is_superadmin:", user.is_superadmin)
                print("is_superuser:", user.is_superuser)
                print("is_staff:", user.is_staff)
                print("role:", user.role)
                if user.is_superadmin:
                    return redirect('superadmin_dashboard')
                return redirect('staff_dashboard')

            messages.error(request, "Access denied")
    else:
        form=StaffLoginForm()
    
    return render(request,'adminpanel/login.html',{"form":form})


@never_cache
@login_required
@user_passes_test(is_admin_user,login_url='staff_login')
def staff_dashboard(request):
    dashboard = DashboardService.get_dashboard_summary()
    return render(request,'adminpanel/staff_dashboard.html',dashboard)
#context dict ayitt thanne pass akune, services nokiya mathi

def home(request):
    return render(request,'adminpanel/home.html')



#study////////////////////////////////
def staff_logout(request):
    logout(request)
    return redirect('home')


@never_cache
@ratelimit(key='ip', rate='5/m', block=True)
def student_login(request):
    form=StudentLoginForm(request.POST or None)

    if request.method=='POST':
        if form.is_valid():
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            
            user=authenticate(request, username=email , password=password )

            if user is not None and user.is_student:
                student = StudentProfile.objects.filter(user=user).first()
                if not student or not student.is_active:
                    messages.error(request, "Your account has been deactivated.")
                    return redirect("student_login")
                login(request,user)
                return redirect('student_dashboard')
            else:
                messages.error(request,"Invalid email or password")

    return render(request,'adminpanel/student_login.html',{'form':form})






# @never_cache
@login_required(login_url='student_login')
@user_passes_test(is_student_user)
def student_dashboard(request):
    student = get_object_or_404(StudentProfile,user=request.user)
    total_fine=student.total_fine()
    return render(
        request,'adminpanel/student_dashboard.html',{'total_fine': total_fine})



@login_required
@user_passes_test(is_admin_user)
def add_student(request):
    form=AddStudentForm(request.POST or None)
    if request.method== "POST" and form.is_valid():
            email=form.cleaned_data['email']  #just to check if email already registered or not

            # if User.objects.filter(email=email).exists():
            #     messages.error(request,"Student with this email id already exist.") #just to check if email already registered or not
            #     return render(request,'adminpanel/add_student.html',{'form':form})  #just to check if email already registered or not
            
            create_student(form.cleaned_data)

            # invalidate dashboard cache
            SafeCache.delete(DASHBOARD_CACHE_KEY)

            messages.success(request,"Student created and email sent sucessfully.")


            # messages.success(request,f"Student added sucessfully. Temporary password: {temp_password}")
            return redirect('staff_students')
    
    return render(request,'adminpanel/add_student.html', {'form':form})


@require_POST
@login_required
@user_passes_test(is_admin_user)
def toggle_student_status(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    student.is_active = not student.is_active
    student.save(update_fields=["is_active"])
    if student.is_active:
        messages.success(request, "Student activated successfully.")
    else:
        messages.success(request, "Student deactivated successfully.")
    return redirect("staff_students")

@never_cache
@login_required
@user_passes_test(is_admin_user)
def staff_students(request):
    courses=Course.objects.all()
    course_id=request.GET.get('course')


    students=StudentProfile.objects.select_related('user','course').order_by('-id')
    if course_id and course_id.isdigit():
        students=students.filter(course_id=int(course_id))

    paginator=Paginator(students,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    context={
            'page_obj':page_obj,
            # 'students':students,
            'courses':courses,
            'selected_course':course_id,
        }
    
    return render(request,'adminpanel/users.html',context)


@require_POST
@never_cache
@login_required
@user_passes_test(is_admin_user)
def delete_student(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    if student.user == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect('staff_students')
    # delete linked user also
    student.user.delete()

    messages.success(request, "Student deleted successfully.")
    return redirect('staff_students')


@require_POST
@login_required
def student_logout(request):
    # Mark all messages as used (flush them)
    # storage = messages.get_messages(request)
    # storage.used = True
    logout(request)
    list(messages.get_messages(request))
    return redirect('home')


@ratelimit(key='ip', rate='3/m', block=True)
def student_forget_password(request):
    if request.method =='POST':
        email=request.POST.get("email")

        user=User.objects.filter(email__iexact=email,role='student',is_active=True).first() 

        if not user:
            messages.error(request,"No student found with this email")
            return redirect('student_forget_password')
        
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))


        reset_link= request.build_absolute_uri(reverse("student_reset_password", kwargs={"uidb64":uidb64,"token":token}))

        send_mail(
            subject="Makbig-Reset your Password",
            message=("You requested to reset your password.\n\n"
            f"Click on this link to reset:\n{reset_link}\n\n"
            "if not requested by you , you can ignore the mail."),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        )

        messages.success(request,"Reset link has been sent")
        
        return redirect('student_login')
    return render (request, 'adminpanel/student_forgot_password.html')


@never_cache
def student_reset_password(request, uidb64, token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        user=User.objects.filter(pk=uid,role='student',is_active=True).first()
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        user= None


    if not user or not default_token_generator.check_token(user,token):
        messages.error(request,"Invalid or expired reset link")
        return redirect('student_login')
    
    #usually used form aan and it is better , but ivide form use akathe kond3 raw input handling
    # if request.method == 'POST':
    # form = ResetPasswordForm(request.POST)
    # if form.is_valid():
    #     password = form.cleaned_data['password']

    
    if request.method=='POST':
        password=request.POST.get("password","").strip()
        confirm_password=request.POST.get("confirm_password","").strip()

        if not password:
            messages.error(request, "Password cannot be empty or spaces only.")
            return redirect(request.path)
        
        if password != confirm_password:
            messages.error(request,"Passwords do not match.")
            return redirect(request.path)
        
        try:
            validate_password(password,user)
        except ValidationError as errors:
            for error in errors:
                messages.error(request,error)
            return redirect (request.path)
        
        user.set_password(password)
        user.save()

        messages.success(request,"Password reset successfully")
        return redirect('student_login')
    
    return render (request,"adminpanel/student_reset_password.html")


@login_required
@never_cache
def student_profile(request):
    try:
        student = get_object_or_404(StudentProfile,user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request,"Student profile not found")
        return redirect("student_dashboard")
    return render(request, "adminpanel/student_profile.html", {"student": student})


def get_started(request):
    return render(request,'adminpanel/get_started.html')



#superadmin


@never_cache
@superadmin_required
def superadmin_dashboard(request):
    # get both datasets independently 
    staff_context = SuperAdminDashboardService.get_dashboard_summary()
    student_context = DashboardService.get_dashboard_summary()

    # merge into one dict,no clashing both are seperate dicts
    context = {**student_context, **staff_context}
    return render(request, 'superadmin/dashboard.html', context)

@never_cache
@superadmin_required
def superadmin_staff_list(request):
    staff_list=User.objects.filter(is_staff=True, is_superuser=False).order_by('first_name')
    return render(request,'superadmin/staff_list.html',{'staff_list':staff_list})


@never_cache
@superadmin_required
def superadmin_add_staff(request):
    if request.method == 'POST':
        form=AddStaffForm(request.POST)
        if form.is_valid():
            form.save()
            invalidate_superadmin_cache()
            messages.success(request,"Staff member created sucessfully")
            return redirect('staff_list')
        else:
            messages.error(request,"Staff adding was unsucessfull")
    else:
        form=AddStaffForm()
    return render(request,'superadmin/add_staff.html',{'form':form})

@never_cache
@superadmin_required
def edit_staff(request,pk):
    staff=get_object_or_404(User, pk=pk, is_staff=True, is_superuser=False)
    # role='staff' guard prevents editing other superadmins via URL manipulation
    if request.method == 'POST':
        form=EditStaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            invalidate_superadmin_cache()
            messages.success(request,f"Staff {staff.get_full_name() or staff.username} details edited sucessfully")
            return redirect('staff_list')
        else:
            messages.error(request,"Staff details editing failed")
    else:
        form=EditStaffForm(instance=staff)
    return render (request,'superadmin/edit_staff.html',{'form':form, 'staff':staff})


@require_POST
@never_cache
@superadmin_required
def toggle_staff(request,pk):
    staff=get_object_or_404(User, pk=pk, is_staff=True, is_superuser=False)
    staff.is_active = not staff.is_active
    staff.save(update_fields=['is_active'])
    invalidate_superadmin_cache()
    status = 'enabled' if staff.is_active else 'disabled'
    messages.success(request, f'"{staff.get_full_name() or staff.username}" has been {status}.')
    return redirect('staff_list')

@never_cache
@superadmin_required
def delete_staff(request,pk):
    staff=get_object_or_404(User, pk=pk , is_staff=True, is_superuser=False)
    if request.method == 'POST':
        if staff == request.user:
            messages.error(request,"You cannot delete yourself.")
            return redirect ('staff_list')
        name = staff.get_full_name() or staff.username
        staff.delete()
        invalidate_superadmin_cache()
        messages.success(request,f"Staff member {name} permanently delete")
        return redirect('staff_list')
    return render(request,'superadmin/confirm_delete.html',{'staff':staff})


@login_required
@user_passes_test(is_admin_user, login_url='staff_login')
def course_list_create(request):

    form = CourseForm()

    if request.method == "POST":
        form = CourseForm(request.POST)

        if form.is_valid():
            CourseService.create_course(form.cleaned_data)
            messages.success(request, "Course added successfully")
            return redirect('course_list')

    courses = CourseService.get_all_courses()

    return render(request,'adminpanel/course_list.html',{'form': form,'courses': courses})


@login_required
@user_passes_test(is_admin_user, login_url='staff_login')
def edit_course(request, course_id):

    course = get_object_or_404(Course, id=course_id)

    form = CourseForm(
        request.POST or None,
        instance=course
    )

    if request.method == "POST" and form.is_valid():

        CourseService.update_course(
            course,
            form.cleaned_data
        )

        messages.success(
            request,
            "Course updated successfully."
        )

        return redirect('course_list')

    return render(
        request,
        'adminpanel/edit_course.html',
        {
            'form': form,
            'course': course
        }
    )

@require_POST
@login_required
@user_passes_test(is_admin_user, login_url='staff_login')
def delete_course(request, course_id):

    course = get_object_or_404(Course, id=course_id)

    try:
        CourseService.delete_course(course)

        messages.success(
            request,
            "Course deleted successfully."
        )

    except ValueError as e:

        messages.error(request, str(e))

    return redirect('course_list')

@login_required
@user_passes_test(is_admin_user)
def edit_student(request, student_id):

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'user',
            'course'
        ),
        id=student_id
    )

    if request.method == "POST":

        form = AddStudentForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            user = student.user

            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.username = data['email']

            user.save()

            student.course = data['course']
            student.save()

            invalidate_dashboard_cache()

            messages.success(
                request,
                "Student updated successfully."
            )

            return redirect('staff_students')

    else:

        form = AddStudentForm(initial={
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
            'course': student.course,
        })

    return render(
        request,
        'adminpanel/edit_student.html',
        {
            'form': form,
            'student': student
        }
    )