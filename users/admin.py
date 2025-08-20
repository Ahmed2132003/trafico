from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

# Inline لعرض Profile داخل صفحة User
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'الملفات الشخصية'

# تخصيص واجهة User في الإدارة
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # الحقول اللي هتظهر في قائمة المستخدمين
    list_display = ('username', 'email', 'user_type', 'phone_number', 'total_earnings', 'is_active', 'is_staff')
    # فلاتر للتصنيف
    list_filter = ('user_type', 'is_active', 'is_staff')
    # البحث بحقول معينة
    search_fields = ('username', 'email', 'phone_number')
    # ترتيب المستخدمين
    ordering = ('username',)
    # الحقول اللي هتظهر في صفحة تعديل المستخدم
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('المعلومات الشخصية', {'fields': ('email', 'phone_number', 'user_type', 'total_earnings')}),
        ('الأذونات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('التواريخ', {'fields': ('last_login', 'date_joined')}),
    )
    # الحقول اللي هتظهر عند إضافة مستخدم جديد
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'user_type', 'password1', 'password2'),
        }),
    )
    # إضافة Profile كـ Inline
    inlines = [ProfileInline]

# تسجيل نموذج Profile لوحده (اختياري)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'date_of_birth')
    search_fields = ('user__username', 'full_name')
    list_filter = ('date_of_birth',)