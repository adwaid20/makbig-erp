from django import forms
from .models import ReviewTicket


class ReviewTicketForm(forms.ModelForm):
    class Meta:
        model = ReviewTicket
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your issue clearly...'
            })
        }
