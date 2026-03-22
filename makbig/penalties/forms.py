from django import forms
from .models import Penalty
from decimal import Decimal

class PenaltyForm(forms.ModelForm):
    class Meta:
        model = Penalty
        fields = ['amount', 'reason']


    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if amount is None:
            return None 

        if amount > Decimal("10000.00"):
            raise forms.ValidationError(
                "Penalty amount cannot exceed ₹10,000."
            )

        if amount < Decimal("0.00"):
            raise forms.ValidationError(
                "Penalty amount cannot be negative."
            )

        return amount



class PenaltyUpdateForm(forms.ModelForm):
    class Meta:
        model = Penalty
        fields = ['amount']