from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='البريد الإلكتروني')
    phone_number = forms.CharField(max_length=15, required=True, label='رقم الهاتف')
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True, label='نوع المستخدم', widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'user_type', 'password1', 'password2']
        labels = {
            'username': 'اسم المستخدم',
            'password1': 'كلمة المرور',
            'password2': 'تأكيد كلمة المرور',
        }