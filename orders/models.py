from django.db import models
from products.models import Product
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_orders', verbose_name=_("المستخدم"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_orders', verbose_name=_("المنتج"))
    # أضف باقي الحقول اللي عندك، زي:
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("الكمية"))
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("السعر الإجمالي"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))

    def __str__(self):
        return f"Order {self.id} for {self.product.name}"