from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from .models import Order

@csrf_exempt
@receiver(valid_ipn_received)
def hook(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == "Completed":
        order = Order.objects.get(id=ipn_obj.invoice)
        customer = order.customer
        customer.number_order_completed += 1
        order.transaction_id = ipn_obj.txn_id
        order.complete = True
        print("IPN PROPERTIES:")
        # dal dizionario si possono ottenere informazioni per confezionare l'ordine e la spedizione, se necessario (shipping = True)
        # address_country: Italy
        # address_city: asd
        # address_country_code: IT
        # address_name: John Doe
        # address_state: BS
        # address_status: confirmed
        # address_street: asd
        # asd
        # address_zip: 12345
        for field, value in ipn_obj.__dict__.items():
            print(f"{field}: {value}")
        
        order.save()
        customer.save()
    return 