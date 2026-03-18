from django import forms 
from .models import Course,StudentProfile
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


User=get_user_model()

name_validator = RegexValidator(regex=r'^[A-Za-z]+$',message="Only alphabetic characters are allowed.")


class StaffLoginForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()


class StudentLoginForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={'palceholder':'Email'}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()


class AddStudentForm(forms.Form):
    first_name=forms.CharField( max_length=100,validators=[name_validator])
    last_name=forms.CharField(max_length=100,validators=[name_validator])
    email=forms.EmailField(max_length=255)
    # password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'password'}))
    course=forms.ModelChoiceField(queryset=Course.objects.all())
    # enrollment_date=forms.DateField()

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")

        return email
    
class AddStaffForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'mobile_number']

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # simple username from email
        user.username = self.cleaned_data['email']

        user.set_password(self.cleaned_data['password'])
        user.role = 'staff'
        user.is_staff = True

        if commit:
            user.save()

        return user