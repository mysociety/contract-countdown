from django import forms


class CouncilChoiceAlertForm(forms.Form):
    CHOICES = [
        ("All UK councils", "All UK councils"),
        ("Councils in a region...", "Councils in a region..."),
        ("My council...", "My council..."),
    ]
    council_choice = forms.CharField(widget=forms.RadioSelect(choices=CHOICES))
