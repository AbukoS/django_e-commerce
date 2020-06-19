from django.db import models
from django_countries.fields import CountryField
from django.shortcuts import reverse
from django.contrib.auth.models import User


LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)
PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'Paypal')
)


class Item(models.Model):
    title = models.CharField(max_length=150)
    price = models.IntegerField()
    discount_price = models.IntegerField(blank=True, null=True)
    slug = models.SlugField()
    description = models.TextField()
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=150, blank=True, null=True)
    rating = models.ForeignKey("Rating", on_delete=models.CASCADE)
    label = models.CharField(choices=LABEL_CHOICES, max_length=2)
    image = models.ImageField(default='default.jpg',
                              upload_to='product_images')

    def __str__(self):
        return self.title

    def get_add_to_cart_url(self):
        return reverse('add_to_cart', kwargs={'slug': self.slug})

    def get_remove_from_cart_url(self):
        return reverse('remove_from_cart', kwargs={'slug': self.slug})

    def get_remove_single_from_cart_url(self):
        return reverse('remove_single_from_cart', kwargs={'slug': self.slug})


class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_amount_saved(self):
        return self.get_item_price() - self.get_item_final_price()

    def get_item_discount_price(self):
        return self.item.discount_price * self.quantity

    def get_item_price(self):
        return self.item.price * self.quantity

    def get_item_final_price(self):
        if self.item.discount_price:
            return self.get_item_discount_price()
        else:
            return self.get_item_price()


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    ordered = models.BooleanField(default=False)
    ref_code = models.CharField(max_length=20)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    address = models.ForeignKey(
        "Address", on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(auto_now=True)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_item_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=250)
    apartment_address = models.CharField(max_length=300, blank=True, null=True)
    country = CountryField(blank_label='(Select country)')
    zip = models.CharField(max_length=5)
    default = models.BooleanField(default=False)
    save_info = models.BooleanField(default=False)
    use_default = models.BooleanField()
    payment_option = models.CharField(choices=PAYMENT_CHOICES, max_length=1)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'


class Payment(models.Model):
    charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=20)
    amount = models.IntegerField()

    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return self.order.user.username


class Category(models.Model):
    name = models.CharField(max_length=200)
    thumbnail = models.ImageField(
        default='default.jpg', upload_to='static/cat_imgs')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Rating(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    value = models.IntegerField(blank=True, null=True)
    message = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.message


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s wishlist"
