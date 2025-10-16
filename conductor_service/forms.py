from django import forms
from .models import ConductorProfile

class ConductorSignupForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, label="Full Name")
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = ConductorProfile
        fields = ['contact_number', 'license_number', 'profile_picture']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ConductorLoginForm(forms.Form):
    employee_id = forms.CharField(max_length=20, label="Employee ID")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
