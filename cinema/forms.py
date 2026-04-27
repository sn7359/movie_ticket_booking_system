from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['customer_name', 'customer_email', 'customer_phone', 'number_of_tickets']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your.email@example.com'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+1234567890'
            }),
            'number_of_tickets': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of tickets',
                'min': '1',
                'max': '10'
            }),
        }
        labels = {
            'customer_name': 'Full Name',
            'customer_email': 'Email Address',
            'customer_phone': 'Phone Number',
            'number_of_tickets': 'Number of Tickets',
        }