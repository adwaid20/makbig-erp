from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from .models import User,StudentProfile,Course
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
# Create your views here.
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
# from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Sum

from penalties.models import Penalty
from .forms import StaffLoginForm,StudentLoginForm,AddStudentForm




User = get_user_model()


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_student_user(user):
    return user.is_authenticated and user.is_student



@never_cache
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
                return redirect(request.GET.get('next', 'staff_dashboard'))

            messages.error(request, "Access denied")
    else:
        form=StaffLoginForm()
    
    return render(request,'adminpanel/login.html',{"form":form})


@never_cache
@login_required
@user_passes_test(is_admin_user,login_url='staff_login')
def staff_dashboard(request):
    return render(request,'adminpanel/staff_dashboard.html')


def home(request):
    return render(request,'adminpanel/home.html')




def staff_logout(request):
    logout(request)
    return redirect('home')


@never_cache
def student_login(request):
    form=StudentLoginForm(request.POST or None)

    if request.method=='POST':
        if form.is_valid():
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            
            user=authenticate(request, username=email , password=password )

            if user is not None and user.is_student:
                login(request,user)
                return redirect('student_dashboard')
            else:
                messages.error(request,"Invalid email or password")

    return render(request,'adminpanel/student_login.html',{'form':form})


# @never_cache
# @login_required
@user_passes_test(is_student_user)
def student_dashboard(request):
    if not request.user.is_student:
        return redirect('home')

    student = request.user.studentprofile

    total_fine = Penalty.objects.filter(student=student).aggregate(total=Sum('amount'))['total'] or 0

    return render(
        request,'adminpanel/student_dashboard.html',{'total_fine': total_fine})



@never_cache
@login_required
@user_passes_test(is_admin_user)
def add_student(request):
    form=AddStudentForm(request.POST or None)
    if request.method=='POST':
        if form.is_valid():
            email=form.cleaned_data['email']

            if User.objects.filter(email=email).exists():
                messages.error(request,"Student with this email id already exist.")
                return render(request,'adminpanel/add_student.html',{'form':form})

            temp_password = get_random_string(8)
            
            user=User.objects.create_user(
                username=email,
                email=email,
                password=temp_password,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_student=True,
                is_staff=False,
            )

            StudentProfile.objects.create(user=user,course=form.cleaned_data['course'],
                # enrollment_date=form.cleaned_data['enrollment_date']
            )

            request.session['new_student_email'] = email
            request.session['new_student_password'] = temp_password

            # messages.success(request,f"Student added sucessfully. Temporary password: {temp_password}")
            return redirect('staff_students')
    
    return render(request,'adminpanel/add_student.html', {'form':form})


@never_cache
@login_required
@user_passes_test(is_admin_user)
def staff_students(request):
    course_id=request.GET.get('course')

    courses=Course.objects.all()

    students=StudentProfile.objects.select_related('user','course')
    if course_id:
        students=students.filter(course_id=course_id)

    temp_password = request.session.pop('new_student_password', None)
    temp_email = request.session.pop('new_student_email', None)

    context={
            'students':students,
            'courses':courses,
            'selected_course':course_id,
            'temp_password': temp_password,
            'temp_email': temp_email,
        }
    
    return render(request,'adminpanel/users.html',context)


@require_POST
@never_cache
@login_required
@user_passes_test(is_admin_user)
def delete_student(request, student_id):
    if not request.user.is_staff:
        return redirect('home')

    student = get_object_or_404(StudentProfile, id=student_id)

    # delete linked user also
    student.user.delete()
    student.delete()  

    messages.success(request, "Student deleted successfully.")
    return redirect('staff_students')


@require_POST
@login_required
def student_logout(request):
    # Mark all messages as used (flush them)
    storage = messages.get_messages(request)
    storage.used = True
    logout(request)
    return redirect('home')


def student_forget_password(request):
    if request.method =='POST':
        email=request.POST.get("email")

        user=User.objects.filter(email=email,is_student=True).first() 

        if not user:
            messages.error(request,"No student found with this email")
            return redirect('student_forget_password')
        
        token = default_token_generator.make_token(user)
        uid=user.pk

        reset_link= request.build_absolute_uri(reverse("student_reset_password", kwargs={"uid":uid,"token":token}))

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


def student_reset_password(request, uid, token):
    user=User.objects.filter(pk=uid, is_student=True).first()

    if not user or not default_token_generator.check_token(user,token):
        messages.error(request,"Invalid or expired rest link")
        return redirect('student_login')
    
    if request.method=='POST':
        password=request.POST.get("password")
        confirm_password=request.POST.get("confirm_password")

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

        messages.success(request,"Password reset sucessfully")
        return redirect('student_login')
    
    return render (request,"adminpanel/student_reset_password.html")


@login_required
def student_profile(request):
    student = StudentProfile.objects.get(user=request.user)
    return render(request, "adminpanel/student_profile.html", {"student": student})