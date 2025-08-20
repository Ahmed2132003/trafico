from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import RegistrationForm
from .models import User, Profile
import random
import string
import time
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

# users/views.py
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # إنشاء كود تحقق عشوائي
            verification_code = ''.join(random.choices(string.digits, k=6))
            # حفظ البيانات مؤقتًا في الجلسة
            request.session['temp_user_data'] = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'user_type': form.cleaned_data['user_type'],
                'password': form.cleaned_data['password1'],
                'verification_code': verification_code,
                'code_timestamp': time.time(),
            }
            # إرسال كود التحقق إلى البريد الإلكتروني
            try:
                send_mail(
                    'Verify Your Trafico Account',
                    f'كود التحقق الخاص بك هو: {verification_code}\nالكود صالح لمدة دقيقتين.',
                    settings.EMAIL_HOST_USER or 'noreply@trafico.com',
                    [form.cleaned_data['email']],
                    fail_silently=False,
                )
                messages.success(request, 'تم إرسال كود التحقق إلى بريدك الإلكتروني. يرجى إدخاله خلال دقيقتين.')
                return redirect('users:verify_email')  # تعديل إلى users:verify_email
            except Exception as e:
                messages.error(request, f'خطأ في إرسال كود التحقق: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.')
    else:
        form = RegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@csrf_protect
def verify_email(request):
    if 'temp_user_data' not in request.session:
        messages.error(request, 'لا توجد بيانات تسجيل. يرجى بدء عملية التسجيل مرة أخرى.')
        return redirect('register')

    if request.method == 'POST':
        entered_code = request.POST.get('verification_code')
        temp_data = request.session['temp_user_data']
        current_time = time.time()
        if current_time - temp_data['code_timestamp'] > 120:  # 2 دقائق
            del request.session['temp_user_data']
            messages.error(request, 'انتهت صلاحية كود التحقق. حاول التسجيل مرة أخرى.')
            return redirect('register')
        if entered_code == temp_data['verification_code']:
            try:
                user = User.objects.create_user(
                    username=temp_data['username'],
                    email=temp_data['email'],
                    password=temp_data['password'],
                    phone_number=temp_data['phone_number'],
                    user_type=temp_data['user_type'],
                    is_active=True,  # تفعيل الحساب بعد التحقق
                )
                # سيتم إنشاء الملف الشخصي تلقائيًا عبر الإشارات
                login(request, user)
                del request.session['temp_user_data']
                messages.success(request, 'تم التسجيل بنجاح! تم إنشاء حسابك.')
                return redirect('dashboard:dashboard')  # تعديل لاستخدام الـ namespace
            except Exception as e:
                messages.error(request, f'خطأ: {str(e)}')
                return redirect('verify_email')
        else:
            messages.error(request, 'كود التحقق غير صحيح.')
    return render(request, 'users/verify_email.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            Profile.objects.get_or_create(user=user)  # التأكد من إنشاء الملف الشخصي
            login(request, user)
            return redirect('dashboard:dashboard')  # تعديل لاستخدام الـ namespace
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    return render(request, 'users/login.html')




def logout_view(request):
    logout(request)
    messages.success(request, ('تم تسجيل الخروج بنجاح!'))
    return redirect('dashboard:dashboard')