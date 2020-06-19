from django.contrib import admin
from .models import (
    Item, OrderItem, Order, Address, Payment, Coupon,
    Refund, Category, Rating, Wishlist
)


def refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


refund_accepted.short_description = 'Update to Refund granted'


def received(modeladmin, request, queryset):
    queryset.update(received=True)


received.short_descritpion = 'Update to Received'


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ['title', 'price', 'discount_price', 'category']
    search_fields = ['title', ]
    list_filter = ['category']
    list_display_links = ('title',)


class AddressAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'street_address',
                    'apartment_address',
                    'default',
                    'country']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'ref_code',
                    'ordered_date',
                    'address',
                    'refund_requested',
                    'refund_granted',
                    'received']
    search_fields = ['user__username', 'ref_code']
    list_filter = [
        'user',
        'ordered',
        'received',
        'refund_requested',
        'refund_granted'
    ]
    actions = [
        refund_accepted,
        received
    ]


class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'order',
        'email',
        'message'
    ]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'charge_id',
                    'amount',
                    'timestamp']


class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'value',
        'message'
    ]
    list_filter = [
        'user',
        'value'
    ]
    search_fields = [
        'value'
    ]


class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'amount']


admin.site.register(Item, ItemAdmin)
admin.site.register(OrderItem)
admin.site.register(Address, AddressAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Category)
admin.site.register(Wishlist)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Refund, RefundAdmin)
