from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import json

class Governorate(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("المحافظة"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("تكلفة الشحن"))

    def __str__(self):
        return self.name

class Design(models.Model):
    designer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'designer'}, verbose_name=_("المصمم"))
    pdf_url = models.URLField(verbose_name=_("رابط ملف PDF"))
    commission_per_sale = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("عمولة البيع لكل قطعة"))
    status = models.CharField(max_length=20, choices=(
        ('pending', 'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'مرفوض'),
    ), default='pending', verbose_name=_("الحالة"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    def save(self, *args, **kwargs):
        if self.commission_per_sale < 5.00 or self.commission_per_sale > 20.00:
            raise ValueError(_("عمولة البيع يجب أن تكون بين 5 و20 جنيه"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Design by {self.designer.username} ({self.status})"

class ProductColor(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='colors', verbose_name=_("المنتج"))
    color = models.CharField(max_length=50, verbose_name=_("اللون"))
    stock = models.PositiveIntegerField(default=0, verbose_name=_("مخزون اللون"))

    def __str__(self):
        return f"{self.color} for {self.product.name}"

class ProductSize(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='sizes', verbose_name=_("المنتج"))
    size = models.CharField(max_length=20, verbose_name=_("المقاس"))
    stock = models.PositiveIntegerField(default=0, verbose_name=_("مخزون المقاس"))

    def __str__(self):
        return f"{self.size} for {self.product.name}"

class Product(models.Model):
    DESIGN_OWNERSHIP_CHOICES = (
        ('site', 'ملكية الموقع'),
        ('designer', 'ملكية مصمم'),
    )
    name = models.CharField(max_length=200, verbose_name=_("اسم المنتج"))
    description = models.TextField(blank=True, verbose_name=_("الوصف"))
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("السعر الأساسي"))
    image = models.URLField(blank=True, null=True, verbose_name=_("صورة المنتج الرئيسية"))
    images = models.JSONField(default=list, blank=True, verbose_name=_("روابط الصور الإضافية"))
    stock = models.PositiveIntegerField(default=0, verbose_name=_("المخزون الكلي"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))
    design = models.ForeignKey(Design, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("التصميم"))
    design_ownership = models.CharField(max_length=20, choices=DESIGN_OWNERSHIP_CHOICES, default='site', verbose_name=_("ملكية التصميم"))
    designer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'user_type': 'designer'}, verbose_name=_("المصمم"))

    def save(self, *args, **kwargs):
        # تحقق من عدد الصور (بين 1 و10)
        if self.images:
            if not isinstance(self.images, list):
                self.images = json.loads(self.images) if isinstance(self.images, str) else []
            if len(self.images) < 1:
                raise ValueError(_("يجب إضافة صورة واحدة على الأقل"))
            if len(self.images) > 10:
                raise ValueError(_("لا يمكن إضافة أكثر من 10 صور"))
            # تحقق من صحة روابط الصور
            for img_url in self.images:
                if not isinstance(img_url, str) or not img_url.strip():
                    raise ValueError(_("جميع الصور يجب أن تكون روابط صالحة"))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites', verbose_name=_("المستخدم"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorites', verbose_name=_("المنتج"))
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإضافة"))

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = _("مفضلة")
        verbose_name_plural = _("المفضلات")

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    marketer_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    marketer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='marketer_cart_items', verbose_name=_("المسوق"))
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("اللون"))
    size = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("المقاس"))

    def total_price(self):
        quantity = Decimal(str(self.quantity))
        return (self.product.base_price * quantity) + (self.marketer_commission * quantity)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} (Qty: {self.quantity}, Color: {self.color or 'N/A'}, Size: {self.size or 'N/A'})"

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_orders', verbose_name=_("المستخدم"))
    customer_name = models.CharField(max_length=200, verbose_name=_("اسم العميل"))
    phone_number = models.CharField(max_length=15, verbose_name=_("رقم الهاتف"))
    secondary_phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("رقم هاتف ثانٍ"))
    governorate = models.ForeignKey(Governorate, on_delete=models.SET_NULL, null=True, verbose_name=_("المحافظة"))
    address = models.TextField(verbose_name=_("العنوان"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات"))
    products = models.ManyToManyField(Product, through='OrderItem', related_name='product_orders', verbose_name=_("المنتجات"))
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("السعر الإجمالي"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    status = models.CharField(max_length=20, choices=(
        ('pending', 'قيد الانتظار'),
        ('shipped', 'تم الشحن'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ), default='pending', verbose_name=_("الحالة"))

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    marketer_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    marketer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='marketer_order_items', verbose_name=_("المسوق"))
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("اللون"))
    size = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("المقاس"))
    designer_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("عمولة المصمم"))

    def total_price(self):
        quantity = Decimal(str(self.quantity))
        return (self.product.base_price * quantity) + (self.marketer_commission * quantity) + (self.designer_commission * quantity)

    def save(self, *args, **kwargs):
        if self.product.design_ownership == 'designer' and self.product.design and self.product.design.status == 'approved':
            self.designer_commission = self.product.design.commission_per_sale
        else:
            self.designer_commission = Decimal('0.00')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} (Qty: {self.quantity}, Color: {self.color or 'N/A'}, Size: {self.size or 'N/A'})"