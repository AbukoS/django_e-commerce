from django import template
from catalog.models import Order

register = template.Library()

@register.filter
def cart_item_count(user):
    if user.is_authenticated:
        order_qs = Order.objects.filter(user=user, ordered=False)
        if order_qs.exists():
            return order_qs[0].items.count()
    return 0
