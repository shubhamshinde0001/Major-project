
from django import forms
from django.forms import inlineformset_factory
from .models import LostAndFound, Bus, Route, Complaint, ComplaintImage

class LostAndFoundForm(forms.ModelForm):
    class Meta:
        model = LostAndFound
        fields = ['description', 'image', 'bus', 'route', 'loss_datetime', 'passenger_name', 'contact_number']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'bus': forms.Select(attrs={'class': 'form-control'}),
            'route': forms.Select(attrs={'class': 'form-control'}),
            'loss_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'passenger_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_contact_number(self):
        contact_number = self.cleaned_data['contact_number']
        if not contact_number.isdigit() or len(contact_number) < 10:
            raise forms.ValidationError("Please enter a valid contact number (at least 10 digits).")
        return contact_number
    

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['description', 'passenger_name', 'contact_number', 'address', 'bus', 'route']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'passenger_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bus': forms.Select(attrs={'class': 'form-control'}),
            'route': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_contact_number(self):
        contact_number = self.cleaned_data['contact_number']
        if not contact_number.isdigit() or len(contact_number) < 10:
            raise forms.ValidationError("Please enter a valid contact number (at least 10 digits).")
        return contact_number

ComplaintImageFormSet = inlineformset_factory(
    Complaint, ComplaintImage, 
    fields=['image'], 
    extra=3,  # Allow up to 3 images
    can_delete=False,
    widgets={'image': forms.FileInput(attrs={'class': 'form-control'})}
)


# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class SignupForm(forms.ModelForm):
    full_name = forms.CharField(max_length=100)
    age_group = forms.ChoiceField(choices=UserProfile.AGE_CHOICES)
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES)
    mobile = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
