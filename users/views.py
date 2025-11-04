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

def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # إنشاء كود تحقق
            verification_code = ''.join(random.choices(string.digits, k=6))
            request.session['reset_password_data'] = {
                'user_id': user.id,
                'verification_code': verification_code,
                'code_timestamp': time.time(),
            }
            # إرسال الكود
            send_mail(
                'كود استعادة كلمة المرور - ترافيكو',
                f'كود التحقق الخاص بك هو: {verification_code}\nالكود صالح لمدة دقيقتين.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'تم إرسال كود التحقق إلى بريدك الإلكتروني.')
            return redirect('users:verify_email')
        except User.DoesNotExist:
            messages.error(request, 'لا يوجد حساب بهذا البريد الإلكتروني.')
        except Exception as e:
            messages.error(request, f'خطأ في إرسال الكود: {str(e)}')
    return render(request, 'users/forget_password.html')


# تعديل verify_email لدعم الـ reset
@csrf_protect
def verify_email(request):
    # تحديد نوع العملية: تسجيل أو استعادة كلمة المرور
    is_reset = 'reset_password_data' in request.session
    temp_data = request.session.get('reset_password_data') or request.session.get('temp_user_data')

    if not temp_data:
        messages.error(request, 'جلسة منتهية. حاول مرة أخرى.')
        return redirect('users:login')

    if request.method == 'POST':
        entered_code = request.POST.get('verification_code')
        current_time = time.time()

        # فحص صلاحية الكود
        if current_time - temp_data['code_timestamp'] > 120:
            if is_reset:
                del request.session['reset_password_data']
            else:
                del request.session['temp_user_data']
            messages.error(request, 'انتهت صلاحية الكود.')
            return redirect('users:login')

        if entered_code == temp_data['verification_code']:
            if is_reset:
                # استعادة كلمة المرور
                del request.session['reset_password_data']
                request.session['reset_user_id'] = temp_data['user_id']
                return redirect('users:reset_password')
            else:
                # تسجيل جديد
                try:
                    user = User.objects.create_user(
                        username=temp_data['username'],
                        email=temp_data['email'],
                        password=temp_data['password'],
                        phone_number=temp_data['phone_number'],
                        user_type=temp_data['user_type'],
                        is_active=True,
                    )
                    login(request, user)
                    del request.session['temp_user_data']
                    messages.success(request, 'تم التسجيل بنجاح!')
                    return redirect('dashboard:dashboard')
                except Exception as e:
                    messages.error(request, f'خطأ: {str(e)}')
        else:
            messages.error(request, 'كود التحقق غير صحيح.')
    return render(request, 'users/verify_email.html', {
        'is_reset': is_reset
    })


def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'جلسة منتهية.')
        return redirect('users:login')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتين.')
        elif len(password1) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.')
        else:
            try:
                user = User.objects.get(id=user_id)
                user.set_password(password1)
                user.save()
                del request.session['reset_user_id']
                login(request, user)  # تسجيل دخول تلقائي
                messages.success(request, 'تم تحديث كلمة المرور بنجاح!')
                return redirect('dashboard:dashboard')
            except User.DoesNotExist:
                messages.error(request, 'المستخدم غير موجود.')
    return render(request, 'users/reset_password.html')

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