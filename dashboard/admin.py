from django.contrib import admin
from .models import WithdrawalRequest, BonusRequest
from django.utils.translation import gettext_lazy as _

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'full_name')
    actions = ['approve_withdrawal', 'fail_withdrawal']

    def approve_withdrawal(self, request, queryset):
        for withdrawal in queryset:
            if withdrawal.status == 'pending' and withdrawal.amount <= withdrawal.user.total_earnings:
                withdrawal.status = 'approved'
                withdrawal.user.total_earnings -= withdrawal.amount
                withdrawal.user.save()
                withdrawal.save()
                self.message_user(request, _(f"تمت الموافقة على طلب السحب {withdrawal.id}"))
            else:
                self.message_user(request, _(f"فشل الموافقة على طلب {withdrawal.id}: المبلغ أكبر من الرصيد أو الطلب ليس قيد المراجعة"), level='error')
    approve_withdrawal.short_description = _("الموافقة على طلبات السحب المحددة")

    def fail_withdrawal(self, request, queryset):
        for withdrawal in queryset:
            if withdrawal.status == 'pending':
                withdrawal.status = 'failed'
                withdrawal.save()
                self.message_user(request, _(f"تم رفض طلب السحب {withdrawal.id}"))
    fail_withdrawal.short_description = _("رفض طلبات السحب المحددة")

@admin.register(BonusRequest)
class BonusRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'completed_orders', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'full_name')
    actions = ['approve_bonus', 'reject_bonus']

    def approve_bonus(self, request, queryset):
        for bonus in queryset:
            if bonus.status == 'pending':
                bonus.status = 'approved'
                bonus.save()
                self.message_user(request, _(f"تمت الموافقة على طلب المكافأة {bonus.id}"))
    approve_bonus.short_description = _("الموافقة على طلبات المكافآت المحددة")

    def reject_bonus(self, request, queryset):
        for bonus in queryset:
            if bonus.status == 'pending':
                bonus.status = 'rejected'
                bonus.save()
                self.message_user(request, _(f"تم رفض طلب المكافأة {bonus.id}"))
    reject_bonus.short_description = _("رفض طلبات المكافآت المحددة")