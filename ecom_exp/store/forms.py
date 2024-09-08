from django import forms
from .models import Customer
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    class Meta:
        model = Customer
        fields = ['email', 'first_name', 'last_name', 'address', 'city', 'password1', 'password2',]

    usable_password = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Customer.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address already registered.")
        return email