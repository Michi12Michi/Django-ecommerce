from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email must be provided.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

class Customer(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    country = models.CharField(_('country'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    city = models.CharField(_('city'), max_length=100)
    address = models.CharField(_('address'), max_length=255)
    zipcode = models.CharField(_('zipcode'), max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    number_order_completed = models.IntegerField(default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'country', 'state', 'city', 'address', 'zipcode',]

    def __str__(self):
        return self.email

    @property
    def has_bonus(self):
        if self.number_order_completed % 10 == 0 or self.number_order_completed == 0:
            return True
        else:
            return False
    
class Product(models.Model):
    name = models.CharField(max_length=200, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    digital = models.BooleanField(default=False, null=True, blank=False)
    # image = models.ImageField(null=True, blank=True, upload_to="media") --> requires Pillow

    def __str__(self) -> str:
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date =  models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, null=True, blank=False)
    transaction_id = models.CharField(max_length=200, default="", null=False)

    def __str__(self) -> str:
        return str(self.id)
    
    @property
    def get_cart_total(self):
        items = self.orderitem_set.all()
        return sum([item.get_total for item in items])
    
    @property
    def get_items_number(self):
        items = self.orderitem_set.all()
        return sum([item.quantity for item in items])
    
    @property
    def shipping(self):
        order_items = self.orderitem_set.all()
        for item in order_items:
            if item.product.digital == False:
                return True
        return False
    
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)

    @property
    def get_total(self):
        return self.quantity*self.product.price
