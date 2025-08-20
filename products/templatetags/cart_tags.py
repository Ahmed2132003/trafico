from django import template

register = template.Library()

@register.filter
def sum_cart_total(cart_items):
    total = sum(item.quantity * item.product.base_price for item in cart_items)
    return total

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0