from django import forms 
from .models import Course,StudentProfile
from django.contrib.auth import get_user_model
User=get_user_model()

class StaffLoginForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    def clean_email(self):
        return self.cleaned_data['email'].lower()

class StudentLoginForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={'palceholder':'Email'}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    def clean_email(self):
        return self.cleaned_data['email'].lower()


class AddStudentForm(forms.Form):
    first_name=forms.CharField()
    last_name=forms.CharField()
    email=forms.EmailField()
    # password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'password'}))
    course=forms.ModelChoiceField(queryset=Course.objects.all())
    # enrollment_date=forms.DateField()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")

        return email