from django import forms
from .models import Penalty
from decimal import Decimal


class BasePenaltyForm(forms.ModelForm):
    amount = forms.DecimalField(required=False)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if amount in [None, ""]:
            return Decimal("0.00")

        if amount > Decimal("10000.00"):
            raise forms.ValidationError("Penalty cannot exceed ₹10,000.")

        if amount < Decimal("0.00"):
            raise forms.ValidationError("Penalty cannot be negative.")

        return amount



class PenaltyForm(BasePenaltyForm):
    class Meta:
        model = Penalty
        fields = ['amount', 'reason']


class PenaltyUpdateForm(BasePenaltyForm):
    class Meta:
        model = Penalty
        fields = ['amount']