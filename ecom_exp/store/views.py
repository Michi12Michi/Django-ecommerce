from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from .models import Order, OrderItem, Product
from .forms import RegisterForm
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
import json

def email_sent(request):
    context = {"no_items": 0}
    return render(request, 'registration/email_sent.html', context)

def activate_account(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return HttpResponse('Activation link is invalid!')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Prepara il link di verifica
            current_site = get_current_site(request)
            verification_link = f"http://{current_site.domain}/activate/{uid}/{token}/"

            # Prepara il contenuto dell'email
            mail_subject = 'Activate your account'
            message = render_to_string('registration/activation_email.html', {
                'user': user,
                'verification_link': verification_link,
            })

            # Invia l'email
            send_mail(
                mail_subject,
                message,
                form.cleaned_data["email"],  # Sostituisci con l'email del mittente
                [user.email],
                fail_silently=False,
            )
            return redirect('email_sent')
        else:
            context = {"form": form, "no_items": 0}
            return render(request, "registration/register.html", context)
    form = RegisterForm()
    context = {"form": form, "no_items": 0}
    return render(request, "registration/register.html", context)

class Login(LoginView):
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_items'] = 0
        return context
    
class Logout(LogoutView):
    next_page = "store"

def store(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        no_items = order.get_items_number
    else:
        no_items = 0
    products = Product.objects.all()
    context = {'products': products, 'no_items': no_items}
    return render(request, 'store/store.html', context)

@login_required
def cart(request):
    customer = request.user
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    total = order.get_cart_total
    no_items = order.get_items_number

    context = {"items": items, "total": total, "no_items": no_items, 'shipping': None}
    return render(request, 'store/cart.html', context)

@login_required
def checkout(request):
    customer = request.user
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    total = order.get_cart_total
    no_items = order.get_items_number
    shipping = order.shipping
    if customer.has_bonus:
        discount_amount = 0.1*float(total)
    else:
        discount_amount = 0
    new_total = float(total) - discount_amount
    paypal_dict = {
        "business": settings.PAYPAL_ADDRESS,
        "amount": total,
        "discount_amount": discount_amount,
        "item_name": f"Order #{order.pk}",
        "invoice": f"{order.pk}",
        "currency_code": 'USD',
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return": request.build_absolute_uri(reverse('payment-success')),
        "cancel_return": request.build_absolute_uri(reverse('payment-cancel')),
        "shopping_url": request.build_absolute_uri(reverse('store'))
    }
    print(f"La spedizione è {shipping}")
    if shipping == True:
        paypal_dict["address_override"] = "1"
        paypal_dict["no_shipping"] =  "2"

    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"items": items, "total": total, "no_items": no_items, 'form': form, 'discount': discount_amount, "new_total": new_total}
    return render(request, 'store/checkout.html', context)

def payment_success(request):
    context = {"no_items": 0}
    return render(request, "store/payment_success.html", context)

def payment_fail(request):
    customer = request.user
    order = Order.objects.get(customer=customer, complete=False)
    no_items = order.get_items_number
    context = {"no_items": no_items}
    return render(request, "store/payment_failed.html", context)

@login_required
def update_item(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            productID = data["productID"]
            action = data["action"]
            customer = request.user
            product = Product.objects.get(id=productID)
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
            if action == "add":
                order_item.quantity += 1
            elif action == "remove":
                order_item.quantity -= 1
            order_item.save()
            if order_item.quantity <= 0:
                order_item.delete()
            order.save()
            return JsonResponse({'message': 'Success'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    