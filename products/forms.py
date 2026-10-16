
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        max_length=254
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2'
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        label='Full Name',
        strip=True
    )

    email = forms.EmailField(
        max_length=254,
        label='Email'
    )

    phone = forms.CharField(
        max_length=15,
        min_length=10,
        label='Phone Number',
        strip=True
    )

    address = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Address',
        strip=True
    )

    city = forms.CharField(
        max_length=100,
        label='City',
        strip=True
    )

    pincode = forms.CharField(
        max_length=10,
        label='Pincode',
        strip=True
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = re.sub(r'\D', '', phone)

        if len(digits) != 10:
            raise forms.ValidationError(
                'Enter a valid 10-digit phone number.'
            )

        return digits

    def clean_pincode(self):
        pincode = self.cleaned_data['pincode']

        if not re.fullmatch(r'\d{6}', pincode):
            raise forms.ValidationError(
                'Enter a valid 6-digit Indian pincode.'
            )

        return pincode
