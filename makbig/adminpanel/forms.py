from django import forms 
from .models import Course,StudentProfile
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

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