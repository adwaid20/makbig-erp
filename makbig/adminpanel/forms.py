from django import forms 
from .models import Course,StudentProfile

class StaffLoginForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))

class StudentLoginForm(forms.Form):
    email=forms.EmailField(widget=forms.EmailInput(attrs={'palceholder':'Email'}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))


class AddStudentForm(forms.Form):
    first_name=forms.CharField()
    last_name=forms.CharField()
    email=forms.EmailField()
    # password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'password'}))
    course=forms.ModelChoiceField(queryset=Course.objects.all())
    # enrollment_date=forms.DateField()