from django import forms
from .models import ReviewAttendance,ReviewSession


class ReviewSessionForm(forms.ModelForm):
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    class Meta:
        model=ReviewSession
        fields=['review_name','scheduled_date','reviewer_name','review_link']


class ReviewAttendanceForm(forms.ModelForm):

    class Meta:
        model = ReviewAttendance
        fields = ['status', 'score', 'remarks']

    def clean_status(self):
        status = self.cleaned_data.get('status')

        # If this is an existing completed review
        if self.instance.pk and self.instance.status in ['pass', 'fail']:
            # Prevent reverting completed review back to upcoming
            if status in ['eligible', 'not_eligible']:
                raise forms.ValidationError(
                    "Completed reviews cannot be reverted to upcoming status."
                )

        return status