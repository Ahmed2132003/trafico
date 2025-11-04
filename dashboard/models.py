from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

class WithdrawalRequest(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('vodafone_cash', _('Vodafone Cash')),
        ('etisalat_cash', _('Etisalat Cash')),
        ('orange_cash', _('Orange Cash')),
        ('we_cash', _('WE Cash')),
        ('bank_transfer', _('تحويل بنكي')),
    )
    STATUS_CHOICES = (
        ('pending', 'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('failed', 'فشل'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawal_requests', verbose_name=_("المستخدم"))
    full_name = models.CharField(max_length=200, verbose_name=_("الاسم الكامل"))
    address = models.TextField(verbose_name=_("العنوان"))
    phone_number = models.CharField(max_length=15, verbose_name=_("رقم الهاتف"))
    wallet_number = models.CharField(max_length=50, verbose_name=_("رقم المحفظة"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='vodafone_cash', verbose_name=_("طريقة السحب"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("المبلغ"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("الحالة"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    def __str__(self):
        return f"Withdrawal {self.id} by {self.user.username} - {self.amount}"
    
class BonusRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'مرفوض'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bonus_requests', verbose_name=_("المستخدم"))
    full_name = models.CharField(max_length=200, verbose_name=_("الاسم الكامل"))
    completed_orders = models.PositiveIntegerField(verbose_name=_("عدد الطلبات المكتملة"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("مبلغ المكافأة"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("الحالة"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    def __str__(self):
        return f"Bonus Request {self.id} by {self.user.username}"