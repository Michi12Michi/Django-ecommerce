from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('login', views.Login.as_view(), name='login'),
    path('logout', views.Logout.as_view(), name='logout'),
    path('register', views.register, name='register'),
    path('email-sent/', views.email_sent, name='email_sent'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate_account'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/', views.cart, name='cart'),
    path('update-item/', views.update_item, name="update-item"),
    path('paypal', include('paypal.standard.ipn.urls')),
    path('checkout/success', views.payment_success, name="payment-success"),
    path('checkout/cancelled', views.payment_fail, name='payment-cancel'),
]