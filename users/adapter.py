from allauth.account.adapter import DefaultAccountAdapter
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailVerificationCode, User
from .forms import CustomSignupForm
import random
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_form_class(self):
        return CustomSignupForm

    def save_user(self, request, user, form, commit=False):
        user = super().save_user(request, user, form, commit=False)
        user.is_active = False  # الحساب غير نشط حتى التحقق
        user.save()

        # إنشاء كود تحقق
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        EmailVerificationCode.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=2)
        )

        # إرسال كود التحقق إلى البريد الإلكتروني
        try:
            send_mail(
                subject='كود تحقق ترافيكو',
                message=f'كود التحقق الخاص بك هو: {code}\nالكود صالح لمدة دقيقتين.',
                from_email=settings.EMAIL_HOST_USER or 'noreply@trafico.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"خطأ في إرسال البريد: {e}")

        # تخزين معرف المستخدم في الجلسة
        request.session['user_id'] = user.id
        return user

    def get_signup_redirect_url(self, request):
        return reverse('verify_email')  # إعادة توجيه إلى /users/verify-email/