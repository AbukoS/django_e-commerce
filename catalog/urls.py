from django.urls import path
from .views import (
    HomeView,
    ProductDetailView,
    OrderSummaryView,
    PaymentView,
    CheckOutView,
    CouponView,
    RefundView,
    ShopBlockView,
    ShopListView,
    add_to_cart,
    payment_complete,
    profile,
    remove_from_cart,
    remove_single_from_cart,
    # Cart
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # path('cart/<slug>/', Cart.as_view(), name='cart'),
    path('add-coupon', CouponView.as_view(), name='add_coupon'),
    path('profile/', profile, name='profile'),
    path('shop/', ShopBlockView.as_view(), name='shop'),
    path('shop-list/', ShopListView.as_view(), name='shop_list'),
    path('request-refund', RefundView.as_view(), name='request_refund'),
    path('detail/<slug>/', ProductDetailView.as_view(), name='detail'),
    path('add-to-cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('remove-single-from-cart/<slug>/',
         remove_single_from_cart, name='remove_single_from_cart'),
    path('order-summary/', OrderSummaryView.as_view(), name='order_summary'),
    path('checkout/', CheckOutView.as_view(), name='checkout'),
    path('payment-complete', payment_complete, name='payment_complete')
]
