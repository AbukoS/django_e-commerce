from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from .models import (
    Item, OrderItem, Order, Address, Payment, Coupon,
    Refund, Category, Wishlist, Rating
)
from .forms import AddressForm, CouponForm, RefundForm

import json
import stripe
import string
import random
import smtplib
import imghdr
from email.message import EmailMessage


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(View):
    def get(self, *args, **kwargs):
        categories = Category.objects.all()[0:3]
        shirts = Item.objects.filter(category__name="Shirt")
        new_products = Item.objects.filter(category__name="New Products")
        context = {
            'categories': categories,
            'shirts': shirts,
            'new_products': new_products
        }
        return render(self.request, 'index.html', context)


class ProductDetailView(DetailView):
    model = Item
    template_name = 'product.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'items': Item.objects.all().order_by('id')[0:3]
        })
        return context

    def post(self, *args, **kwargs):
        print(self.request.POST)
        return redirect('cart')


class Cart(View):
    def get(self, *args, **kwargs):
        return render(self.request, 'cart.html')


class ShopBlockView(View):
    def get(self, *args, **kwargs):
        context = {
            'items': Item.objects.all()
        }
        return render(self.request, 'shop.html', context)


class ShopListView(View):
    def get(self, *args, **kwargs):
        context = {
            'items': Item.objects.all()
        }
        return render(self.request, 'shop_list.html', context)


class CheckOutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = AddressForm()
            coupon_form = CouponForm()
            context = {
                'form': form,
                'order': order,
                'coupon_form': coupon_form,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You don't have an active order")
            return redirect('order_summary')

    def post(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = AddressForm(self.request.POST or None)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                use_default = form.cleaned_data.get('use_default')

                address = Address(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                    use_default=use_default
                )
                address.save()
                order.address = address
                order.save()

                save_info = form.cleaned_data.get('save_info')
                if save_info:
                    address.default = True
                    address.save()

                use_default = form.cleaned_data.get('use_default')
                if use_default:
                    address_qs = Address.objects.get(
                        user=self.request.user, default=True)
                    if address_qs.exists():
                        address = address_qs[0]
                        order.address = address
                        order.save()
                # return redirect('checkout')
                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == 'S':
                    return redirect('payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('payment', payment_option='paypal')
                else:
                    messages.info(
                        self.request, 'Invalid payment option selected!')
                    return redirect('checkout')
        except ObjectDoesNotExist:
            messages.info(self.request, "You don't have an active order!")
            return redirect('order_summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if order.address is not None:
                context = {
                    'order': order,
                    'DISPLAY_COUPON_FORM': False
                }
                return render(self.request, 'pay.html', context)
            else:
                messages.info(
                    self.request, "Please provide a shipping address")
                return redirect('checkout')
        except ObjectDoesNotExist:
            messages.info(self.request, "You don't have an active order")
            return redirect('order_summary')

    def post(self, *args, **kwargs):
        to_email = self.request.user.email
        print('customer email -->', to_email)
        order = Order.objects.get(user=self.request.user, ordered=False)
        try:
            customer = stripe.Customer.create(
                name=self.request.user,
                email=self.request.user.email,
                source=self.request.POST['stripeToken']

            )
            amount = int(order.get_total() * 100)
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                customer=customer,
                description="My first own test"
            )
            payment = Payment()
            payment.charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                print(item.item.title)
                print(item.item.discount_price)
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            # msg = EmailMessage()
            # msg['Subject'] = f'Your order{item.item.title}'
            # msg['From'] = "Butek's Online <buteksonline@gmail.com>"
            # msg['To'] = to_email
            # msg.set_content(
            #     f"Testing{item.item.title} for {item.item.discount_price} to be shipped to {order.address.street_address} the new feature of buteks online {item.item.image.url}")

            # msg.add_alternative(
            #     """
            #     <!DOCTYPE html>
            #     <html lang="en">
            #         <body>
            #             <h1 style="color:gray;">Helloh</h1>
            #             <img src='catalog/img.jpg' alt="itemimg">
            #         </body>
            #     </html>
            #     """
            # , subtype='html')

            # with open(f'media/{item.item.image}', 'rb') as f:
            #     file_data = f.read()
            #     file_type = imghdr.what(f.name)
            #     file_name = f.name

            # msg.add_attachment(file_data, maintype='image',
            #                    subtype=file_type, filename=file_name)

            # with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            #     username = ""
            #     password = ""
            #     smtp.login(username, password)

            #     smtp.send_message(msg)

            messages.success(
                self.request, 'Your payment was successful. Go to you profile to view the deilvery status')
            return redirect('home')

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.info(self.request, f"{err.get('message')}")
            return redirect('/')
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.info(self.request, "Rate limit error")
            return redirect('/')
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.info(self.request, "Invalid parameters")
            return redirect('/')
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.info(self.request, "Not authenticated")
            return redirect('/')
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.info(
                self.request, "Connection error...Please check your connection")
            return redirect('/')
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.info(
                self.request, "Something went wrong, You were not charged. Please try again")
            return redirect('/')
        except Exception as e:
            # Send an e-mail to ourselves
            print(e)
            messages.info(
                self.request, "A serious error occurred, We were notified and are handling it.")
            return redirect('/')


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'objects': order
            }
            return render(self.request, 'cart.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You don't have an active order!")
            return redirect('home')


class CouponView(View):
    def post(self, *args, **kwargs):
        coupon_form = CouponForm(self.request.POST or None)
        if coupon_form.is_valid():
            try:
                code = coupon_form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = Coupon.objects.get(code=code)
                order.save()
                messages.success(self.request, 'Successfully added coupon!')
                return redirect('checkout')
            except ObjectDoesNotExist:
                messages.info(self.request, "You don't have an active order!")
                return redirect('checkout')


class RefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, 'refund.html', context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email'),
            code = form.cleaned_data.get('code'),
            reason = form.cleaned_data.get('reason')
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(ref_code=code, ordered=True)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.email = email
                refund.message = reason
                refund.save()
                messages.success(
                    self.request, "You refund request has been received and is being processed!")
                return redirect('home')
            except ObjectDoesNotExist:
                messages.info(
                    self.request, "This order does not exist! Enter the correct reference code")
                return redirect('request_refund')
        messages.warning(
            self.request, "Please enter the correct order reference code")
        return redirect('request_refund')


def payment_complete(request):
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, ordered=False, id=body['order_id'])

    # create the payment
    payment = Payment()
    payment.charge_id = create_ref_code()
    payment.user = request.user
    payment.amount = order.get_total()
    payment.save()

    order_items = order.items.all()
    order_items.update(ordered=True)
    for item in order_items:
        item.save()

    # assign the payment to the order
    order.ordered = True
    order.payment = payment
    order.ref_code = create_ref_code()
    order.save()
    messages.success(
        request, 'Your payment was successful. Go to you profile to view the deilvery status')
    return redirect('home')


def profile(request):
    context = {
        'orders': Order.objects.filter(user=request.user).order_by('-ordered_date')
    }
    return render(request, 'profile.html', context)


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.success(request, f"{item}'s quantity was updated")
            return redirect('order_summary')
        else:
            order.items.add(order_item)
            messages.success(request, f"{item} was added to your cart")
            return redirect('order_summary')
    else:
        # ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered=False)  # ordered_date=ordered_date)
        order.items.add(order_item)
        messages.success(request, f"{item} was added to your cart")
        return redirect('order_summary')


@login_required
def remove_single_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order.save()
            messages.success(request, f"{item}'s quantity was updated!")
            return redirect('order_summary')

        else:
            messages.success(request, f"{item} was not in your cart")
            return redirect('detail', slug=slug)
    else:
        messages.success(request, "You do not have an active order")
        return redirect('detail', slug=slug)


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False)[0]

            order.items.remove(order_item)
            messages.success(request, f"{item} was removed from your cart!")
            return redirect('order_summary')

        else:
            messages.success(request, f"{item} was not in your cart")
            return redirect('detail', slug=slug)
    else:
        messages.success(request, "You do not have an active order")
        return redirect('detail', slug=slug)
